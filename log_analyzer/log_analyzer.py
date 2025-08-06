import argparse
import gzip
import json
import logging
import os
import re
import sys
from collections.abc import Generator
from datetime import datetime
from string import Template

import structlog
from structlog.stdlib import LoggerFactory

from log_analyzer.entities import Config, LogInfo, RawLog, UriStatistics

LOG_FILES_PATTERN = r"nginx-access-ui.log-(\d{8})(?:\.gz)?$"
REPORT_FILE_NAME_TEMPLATE = "report-$year.$month.$day.html"

logger: structlog.BoundLogger


def parse_config() -> str | None:
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", help="allow specifying custom configuration file", type=str)
    args = args_parser.parse_args()
    return args.config if args.config else None


def merge_config(default_config: Config, external_config_path: str | None) -> Config:
    if not external_config_path:
        return default_config

    if not os.path.exists(external_config_path):
        raise FileNotFoundError(f"Config file {external_config_path} not found")

    with open(external_config_path) as config_file:
        config_data = json.load(config_file)

    return Config(
        log_dir=config_data.get("LOG_DIR") or default_config.log_dir,
        report_dir=config_data.get("REPORT_DIR") or default_config.report_dir,
        report_size=config_data.get("REPORT_SIZE") or default_config.report_size,
        report_template_path=config_data.get("REPORT_TEMPLATE_PATH") or default_config.report_template_path,
        logging_path=config_data.get("LOGGING_PATH") or default_config.logging_path,
        failure_threshold=config_data.get("FAILURE_THRESHOLD") or default_config.failure_threshold,
    )


def get_last_log_file_name(log_folder_path: str) -> LogInfo | None:
    latest_log_file = None
    latest_log_date = None

    if not os.path.exists(log_folder_path):
        raise ValueError(f"Log folder {log_folder_path} does not exist")

    for file in os.scandir(log_folder_path):
        file_match = re.match(LOG_FILES_PATTERN, file.name)
        if not file_match:
            continue
        current_date = file_match.group(1)
        if latest_log_date is None or current_date > latest_log_date:
            latest_log_date = current_date
            latest_log_file = file.path

    if not latest_log_date or not latest_log_file:
        return None

    _, file_ext = os.path.splitext(latest_log_file)

    return LogInfo(
        log_date=datetime.strptime(latest_log_date, "%Y%m%d"),
        file_name=latest_log_file,
        file_ext=file_ext,
    )


def read_log_file(log_file_path: str, log_file_ext: str | None) -> Generator[str]:
    with (
        gzip.open(log_file_path, "rt", encoding="utf-8")
        if log_file_ext and log_file_ext == ".gz"
        else open(log_file_path, encoding="utf-8") as log_file
    ):
        yield from log_file.readlines()


def analyze_logs(log_line_gen: Generator[str], config: Config) -> list[UriStatistics]:
    report_data: dict[str, UriStatistics] = {}
    total_line_count = 0
    total_request_time = 0.0
    failed_logs = 0
    for log_line in log_line_gen:
        try:
            log_entry = RawLog.from_str(log_line)
            total_line_count += 1
            total_request_time += log_entry.request_time
            report_entry = report_data.get(log_entry.request, None)
            is_updated, report_entry = UriStatistics.update_statistics(
                report_entry, log_entry, total_line_count, total_request_time
            )
            if not is_updated or not report_entry:
                failed_logs += 1
                continue
            report_data[log_entry.request] = report_entry
        except Exception:
            failed_logs += 1
            continue

    if failed_logs / total_line_count > config.failure_threshold:
        raise Exception("Too many failed logs")

    return list(report_data.values())


def generate_report_file_name(log_date: datetime) -> str:
    return Template(REPORT_FILE_NAME_TEMPLATE).substitute(
        year=log_date.year, month=log_date.month, day=log_date.day
    )


def generate_report(report_file_name: str, processed_logs: list[UriStatistics], config: Config) -> None:
    sorted_logs = sorted(processed_logs, key=lambda x: x.time_sum, reverse=True)
    json_logs = json.dumps([log.to_dict() for log in sorted_logs[: config.report_size]])

    with open(config.report_template_path, encoding="utf-8") as report_template:
        report_file_template = report_template.read()
    template = Template(report_file_template)

    file_content = template.safe_substitute(table_json=json_logs)

    report_path = os.path.join(config.report_dir, report_file_name)
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(file_content)


def setup_logging(logging_path: str) -> None:
    if not os.path.exists(logging_path):
        os.makedirs(logging_path)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(logging_path, "log_analyzer.log")),
        ],
    )
    structlog.configure(
        logger_factory=LoggerFactory(),
        processors=[
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False, key="timestamp"),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.KeyValueRenderer(key_order=["timestamp", "event", "exception"]),
        ],
    )


def main() -> None:
    try:
        config = Config(
            log_dir="./data/log",
            report_dir="./data/report",
            report_size=1000,
            report_template_path="./data/report.html",
            logging_path="./logs",
            failure_threshold=0.3,
        )
        setup_logging(config.logging_path)

        global logger
        logger = structlog.get_logger()

        logger.info("Starting log analyzer")

        args_config_path = parse_config()
        config = merge_config(config, args_config_path)
        logger.debug(f"Config: {config}")

        config.validate()
        setup_logging(config.logging_path)

        last_log_info = get_last_log_file_name(config.log_dir)
        logger.info(f"Last log info: {last_log_info}")

        if not last_log_info:
            logger.info("No log files provided in the log directory")
            sys.exit(0)

        report_file_name = generate_report_file_name(last_log_info.log_date)
        if os.path.exists(os.path.join(config.report_dir, report_file_name)):
            logger.info(f"Report file {report_file_name} already exists")
            sys.exit(0)
        logger.info(f"Report file name: {report_file_name}")

        processed_logs = analyze_logs(read_log_file(last_log_info.file_name, last_log_info.file_ext), config)
        generate_report(report_file_name, processed_logs, config)
        logger.info("Report file generated")
    except KeyboardInterrupt:
        logger.error("User exited the program", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
