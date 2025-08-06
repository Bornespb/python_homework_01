import sys

import pytest

from log_analyzer.entities import Config, JsonConfig
from log_analyzer.log_analyzer import get_last_log_file_name, merge_config, parse_config


def _get_default_config() -> Config:
    return Config.from_dict(
        JsonConfig(
            LOG_DIR="./data/log",
            REPORT_DIR="./data/report",
            REPORT_SIZE=1000,
            REPORT_TEMPLATE_PATH="./data/report.html",
            LOGGING_PATH="./logs",
            FAILURE_THRESHOLD=0.3,
        )
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
