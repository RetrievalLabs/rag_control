VENV_DIR := .venv
PYTHON := python3

.PHONY: venv activate install install-dev sync sync-dev test clean

venv:
	uv venv $(VENV_DIR) --python $(PYTHON)

activate: 
	@echo "Run this in your shell:"
	@echo "source $(VENV_DIR)/bin/activate"

install: 
	uv pip install --python $(VENV_DIR)/bin/python -e .

install-dev: 
	uv pip install --python $(VENV_DIR)/bin/python -e ".[dev]"

sync: install

sync-dev: install-dev

test: install-dev
	uv run --python $(VENV_DIR)/bin/python pytest -q

clean:
	rm -rf $(VENV_DIR)
