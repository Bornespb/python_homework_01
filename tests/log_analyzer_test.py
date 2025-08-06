import json
import sys

import pytest

from log_analyzer.entities import Config, JsonConfig
from log_analyzer.log_analyzer import get_last_log_file_name, merge_config, parse_config


def _get_default_config() -> Config:
    with open("./data/config.json") as config_file:
        config_data = json.load(config_file)
        return Config.from_dict(
            JsonConfig(
                LOG_DIR=config_data.get("LOG_DIR"),
                REPORT_DIR=config_data.get("REPORT_DIR"),
                REPORT_SIZE=config_data.get("REPORT_SIZE"),
                REPORT_TEMPLATE_PATH=config_data.get("REPORT_TEMPLATE_PATH"),
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
