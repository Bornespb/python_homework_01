import json

import pytest

from log_analyzer.entities import Config, JsonConfig


def _get_default_config_json() -> JsonConfig:
    with open("./data/config.json") as config_file:
        config_data = json.load(config_file)
        return JsonConfig(
            LOG_DIR=config_data.get("LOG_DIR"),
            REPORT_DIR=config_data.get("REPORT_DIR"),
            REPORT_SIZE=config_data.get("REPORT_SIZE"),
            REPORT_TEMPLATE_PATH=config_data.get("REPORT_TEMPLATE_PATH"),
        )


def test_default_config() -> None:
    config = Config.from_dict(_get_default_config_json())
    assert config.log_dir == "./log"
    assert config.report_dir == "./report"
    assert config.report_size == 1000
    assert config.report_template_path == "./data/report.html"


def test_from_dict() -> None:
    config = Config.from_dict(_get_default_config_json())
    assert config.log_dir == "./log"
    assert config.report_dir == "./report"
    assert config.report_size == 1000
    assert config.report_template_path == "./data/report.html"


def test_validate_config_invalid_log_dir() -> None:
    config_json = _get_default_config_json()
    config_json["LOG_DIR"] = "./invalid_log_dir"
    with pytest.raises(ValueError):
        Config.from_dict(config_json)


def test_validate_config_invalid_report_dir() -> None:
    config_json = _get_default_config_json()
    config_json["REPORT_DIR"] = "./invalid_report_dir"
    with pytest.raises(ValueError):
        Config.from_dict(config_json)


def test_validate_config_invalid_report_template_path() -> None:
    config_json = _get_default_config_json()
    config_json["REPORT_TEMPLATE_PATH"] = "./invalid_report_template_path"
    with pytest.raises(ValueError):
        Config.from_dict(config_json)
