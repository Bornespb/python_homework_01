import argparse
import gzip
import json
import os
import re
import sys
from collections.abc import Generator
from datetime import datetime
from string import Template

from log_analyzer.entities import Config, JsonConfig, LogInfo, RawLog, UriStatistics

LOG_FILES_PATTERN = r"nginx-access-ui.log-(\d{8})(?:\.gz)?$"
REPORT_FILE_NAME_TEMPLATE = "report-$year.$month.$day.html"
DEFAULT_CONFIG_PATH = "./data/config.json"


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
    )


def get_last_log_file_name(log_folder_path: str) -> LogInfo:
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
        raise ValueError(f"No log files provided in the {log_folder_path} folder.")

    _, file_ext = os.path.splitext(latest_log_file)

    return LogInfo(
        log_date=datetime.strptime(latest_log_date, "%Y%m%d"),
        file_name=latest_log_file,
        file_ext=file_ext,
    )


def read_log_file(log_file_path: str, log_file_ext: str | None) -> Generator[str]:
    with (
        gzip.open(log_file_path, "rt")
        if log_file_ext and log_file_ext == ".gz"
        else open(log_file_path) as log_file
    ):
        yield from log_file.readlines()


def analyze_logs(log_line_gen: Generator[str]) -> list[UriStatistics]:
    report_data: dict[str, UriStatistics] = {}
    total_line_count = 0
    total_request_time = 0.0
    failed_logs = 0
    for log_line in log_line_gen:
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
    return list(report_data.values())


def generate_report(log_date: datetime, processed_logs: list[UriStatistics], config: Config) -> None:
    filtered_logs = list(filter(lambda x: x.time_sum > config.report_size, processed_logs))
    sorted_logs = sorted(filtered_logs, key=lambda x: x.time_sum, reverse=True)
    json_logs = json.dumps([log.to_dict() for log in sorted_logs])

    with open(config.report_template_path) as report_template:
        report_file_template = report_template.read()
    template = Template(report_file_template)

    file_content = template.safe_substitute(table_json=json_logs)

    report_file_name = Template(REPORT_FILE_NAME_TEMPLATE).substitute(
        year=log_date.year, month=log_date.month, day=log_date.day
    )

    report_path = os.path.join(config.report_dir, report_file_name)
    with open(report_path, "w") as report_file:
        report_file.write(file_content)


def main() -> None:
    try:
        if not os.path.exists(DEFAULT_CONFIG_PATH):
            raise FileNotFoundError(f"Config file {DEFAULT_CONFIG_PATH} not found")
        with open(DEFAULT_CONFIG_PATH) as config_file:
            config_data = json.load(config_file)
            config = Config.from_dict(
                JsonConfig(
                    LOG_DIR=config_data.get("LOG_DIR"),
                    REPORT_DIR=config_data.get("REPORT_DIR"),
                    REPORT_SIZE=config_data.get("REPORT_SIZE"),
                    REPORT_TEMPLATE_PATH=config_data.get("REPORT_TEMPLATE_PATH"),
                )
            )

        args_config_path = parse_config()
        config = merge_config(config, args_config_path)

        last_log_info = get_last_log_file_name(config.log_dir)

        processed_logs = analyze_logs(read_log_file(last_log_info.file_name, last_log_info.file_ext))
        generate_report(last_log_info.log_date, processed_logs, config)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
