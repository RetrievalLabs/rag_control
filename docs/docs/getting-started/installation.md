---
title: Installation
description: How to install and set up rag_control
---

# Installation

## Requirements

- **Python**: 3.9+
- **Package Manager**: pip or poetry

## Core Dependencies

rag_control requires the following packages:

```
pydantic>=2.0         # Data validation
pyyaml>=6.0           # Configuration parsing
structlog>=23.0       # Structured logging
opentelemetry-api>=1.15        # Distributed tracing (optional)
opentelemetry-sdk>=1.15        # Distributed tracing (optional)
```

## Install from PyPI

```bash
pip install rag_control
```

## Install for Development

If you want to contribute or run tests locally:

```bash
git clone https://github.com/RetrievalLabs/rag_control.git
cd rag_control

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with all dependencies
pip install -e ".[dev,test]"
```

## Verify Installation

```python
import rag_control
print(rag_control.__version__)
```

Or check that the core module imports:

```bash
python -c "from rag_control.core.engine import RAGControl; print('Installation successful!')"
```

## Optional Dependencies

### Distributed Tracing (OpenTelemetry)

For production observability:

```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-jaeger  # Jaeger exporter
# or
pip install opentelemetry-exporter-otlp  # OTLP exporters
```

### Development Tools

For running tests and quality checks:

```bash
pip install pytest pytest-cov black ruff mypy
```

## Next Steps

1. **Quick Start**: Learn the basics with [Quick Start Guide](/getting-started/quick-start)
2. **Configuration**: Understand how to configure rag_control with [Configuration Guide](/getting-started/configuration)
3. **Core Concepts**: Dive deeper into [Core Concepts](/concepts/overview)

## Troubleshooting

### ModuleNotFoundError: No module named 'rag_control'

Ensure rag_control is installed:
```bash
pip list | grep rag_control
pip install rag_control
```

### Pydantic version conflicts

rag_control requires Pydantic v2. If you have conflicts:
```bash
pip install --upgrade pydantic
```

### OpenTelemetry import issues

OpenTelemetry is optional. If you see import errors but don't need tracing:
- Skip the OpenTelemetry optional dependency
- Use the `NoOpTracingProvider` in configuration

## Getting Help

- Check [DEVELOPMENT.md](https://github.com/RetrievalLabs/rag_control/blob/main/DEVELOPMENT.md) for setup issues
- Open an [issue on GitHub](https://github.com/RetrievalLabs/rag_control/issues)
