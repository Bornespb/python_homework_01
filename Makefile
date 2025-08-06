.PHONY: lint test test-cov
pre-commit:
	pre-commit run --all-files

test:
	pytest tests

test-cov:
	pytest tests --cov=log_analyzer --cov-report term

run:
	python log_analyzer/log_analyzer.py ${PARAMS}
