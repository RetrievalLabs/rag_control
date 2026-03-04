---
title: Development Setup
description: Setting up your development environment
---

# Development Setup

## Prerequisites

- Python 3.9+
- Git
- pip or poetry

## Clone Repository

```bash
git clone https://github.com/RetrievalLabs/rag_control.git
cd rag_control
```

## Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Install Dependencies

```bash
# Install in editable mode with all development dependencies
pip install -e ".[dev,test]"

# Or using poetry
poetry install
```

## Install Pre-commit Hooks

```bash
pre-commit install
```

## Verify Installation

```bash
# Run tests
pytest

# Run type checking
mypy --strict rag_control

# Run linting
ruff check rag_control

# Check formatting
black --check rag_control
```

## Common Development Tasks

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_engine.py

# Run with coverage
pytest --cov=rag_control

# Run in verbose mode
pytest -v
```

### Type Checking

```bash
# Check types (strict mode)
mypy --strict rag_control

# Check with configuration
mypy --config-file pyproject.toml
```

### Code Formatting

```bash
# Format code
black rag_control

# Check formatting
black --check rag_control
```

### Linting

```bash
# Lint code
ruff check rag_control

# Fix auto-fixable issues
ruff check --fix rag_control
```

## Running Documentation Locally

From the `docs/` directory:

```bash
cd docs

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

Documentation will be available at `http://localhost:3000`

## IDE Setup

### VS Code

Install extensions:
- Python
- Pylance
- Black Formatter
- Ruff

### PyCharm

- Installed Python interpreter set to `.venv`
- Enable type checking (Settings → Tools → Python → Type Checking)

## See Also

- [Testing Guide](/development/testing)
- [Contributing Guide](/development/contributing)
- [Development Docs](https://github.com/RetrievalLabs/rag_control/blob/main/DEVELOPMENT.md)
