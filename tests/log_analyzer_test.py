import sys

import pytest

from log_analyzer.entities import Config
from log_analyzer.log_analyzer import get_last_log_file_name, merge_config, parse_config


def _get_default_config() -> Config:
    return Config(
        log_dir="./data/log",
        report_dir="./data/report",
        report_size=1000,
        report_template_path="./data/report.html",
        logging_path="./logs",
        failure_threshold=0.3,
    )


def test_parse_config() -> None:
    sys.argv = ["log_analyzer.py"]
    assert parse_config() is None


def test_merge_config() -> None:
    default_config = _get_default_config()
    merge_config(default_config, None)


def test_merge_config_invalid_config_file() -> None:
    with pytest.raises(FileNotFoundError):
        default_config = _get_default_config()
        merge_config(default_config, "./invalid_config.json")


def test_get_last_log_file_name() -> None:
    with pytest.raises(ValueError):
        get_last_log_file_name("")
