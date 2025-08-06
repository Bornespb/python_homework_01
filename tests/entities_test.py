import pytest

from log_analyzer.entities import Config, JsonConfig


def _get_default_config_json() -> JsonConfig:
    return JsonConfig(
        LOG_DIR="./data/log",
        REPORT_DIR="./data/report",
        REPORT_SIZE=1000,
        REPORT_TEMPLATE_PATH="./data/report.html",
        LOGGING_PATH="./logs",
        FAILURE_THRESHOLD=0.3,
    )


def test_default_config() -> None:
    config = Config.from_dict(_get_default_config_json())
    assert config.log_dir == "./data/log"
    assert config.report_dir == "./data/report"
    assert config.report_size == 1000
    assert config.report_template_path == "./data/report.html"
    assert config.logging_path == "./logs"
    assert config.failure_threshold == 0.3


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
