VENV_DIR := .venv
PYTHON := python3

.PHONY: venv activate install install-dev sync sync-dev test tests unit-test coverage lint format typecheck docs-clean docs-install docs-build docs-start clean

venv:
	uv venv $(VENV_DIR) --python $(PYTHON)

activate: 
	@echo "Run this in your shell:"
	@echo "source $(VENV_DIR)/bin/activate"

install:
	uv sync --python $(VENV_DIR)/bin/python


install-dev:
	uv sync --python $(VENV_DIR)/bin/python --group dev

sync: install

sync-dev: install-dev

test: install-dev
	uv run --python $(VENV_DIR)/bin/python pytest -v

tests: test

unit-test: install-dev
	uv run --python $(VENV_DIR)/bin/python pytest -v tests/unit

coverage: install-dev
	uv run --python $(VENV_DIR)/bin/python pytest -v --cov=rag_control --cov-report=term-missing --cov-report=xml --cov-report=html

lint: install-dev
	uv run --python $(VENV_DIR)/bin/python ruff check .

format: install-dev
	uv run --python $(VENV_DIR)/bin/python ruff format .
	uv run --python $(VENV_DIR)/bin/python black .

typecheck: install-dev
	uv run --python $(VENV_DIR)/bin/python mypy .


docs-clean:
	rm -rf docs/build docs/site docs/_build 2>/dev/null; \
	echo "Documentation build artifacts cleaned"

docs-install:
	cd docs && npm install

docs-build:
	cd docs && npm run build

docs-start:
	cd docs && npm start

clean:
	rm -rf $(VENV_DIR)
