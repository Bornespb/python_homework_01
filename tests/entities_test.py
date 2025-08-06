import pytest

from log_analyzer.entities import Config


def _get_default_config() -> Config:
    return Config(
        log_dir="./data/log",
        report_dir="./data/report",
        report_size=1000,
        report_template_path="./data/report.html",
        logging_path="./logs",
        failure_threshold=0.3,
    )


def test_default_config() -> None:
    config = _get_default_config()
    assert config.log_dir == "./data/log"
    assert config.report_dir == "./data/report"
    assert config.report_size == 1000
    assert config.report_template_path == "./data/report.html"
    assert config.logging_path == "./logs"
    assert config.failure_threshold == 0.3


def test_validate_config_invalid_report_template_path() -> None:
    config = _get_default_config()
    config.report_template_path = "./invalid_report_template_path"
    with pytest.raises(ValueError):
        config.validate()
