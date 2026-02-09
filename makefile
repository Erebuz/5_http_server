VENV = .venv
BIN = $(VENV)/Scripts
PYTHON = $(BIN)/python

PROJECT_NAME = 3_api_validator

.PHONY: run lint

lint:
	pre-commit run --all-files --color=never

test:
	python -m unittest discover -s ./tests/
