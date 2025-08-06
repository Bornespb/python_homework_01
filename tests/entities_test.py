from log_analyzer.entities import Config


def test_default_config() -> None:
    config = Config.get_default_config()
    assert config.log_dir == "./log"
    assert config.report_dir == "./report"
    assert config.report_size == 1000
    assert config.report_template_path == "./data/report.html"


def test_from_dict() -> None:
    config = Config.from_dict(
        {
            "LOG_DIR": "./log",
            "REPORT_DIR": "./report",
            "REPORT_SIZE": 1000,
            "REPORT_TEMPLATE_PATH": "./data/report.html",
        }
    )
    assert config.log_dir == "./log"
    assert config.report_dir == "./report"
    assert config.report_size == 1000
    assert config.report_template_path == "./data/report.html"
