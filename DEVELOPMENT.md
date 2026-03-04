# Development Guide for rag_control

## Overview

`rag_control` is a runtime governance, security, and execution control layer for Retrieval-Augmented Generation (RAG) systems. This guide covers local development setup, testing, code quality checks, and contributing guidelines.

## Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management

## Development Setup

### 1. Create Virtual Environment

```bash
make venv
source .venv/bin/activate
```

Alternatively, using uv directly:
```bash
uv venv
source .venv/bin/activate
```

### 2. Install Dependencies

Install all dependencies including development tools:
```bash
make install-dev
```

This installs:
- Project dependencies: `pydantic`, `pyyaml`, `structlog`, `opentelemetry-api`, `opentelemetry-sdk`
- Dev dependencies: `pytest`, `pytest-cov`, `ruff`, `black`, `mypy`

## Running Tests

### Run All Tests
```bash
make test
```

### Run Unit Tests Only
```bash
make unit-test
```

### Generate Coverage Report
```bash
make coverage
```

This generates:
- Terminal output with missing line coverage
- XML coverage report for CI/CD integration
- HTML coverage report in `htmlcov/` directory

**Note**: The project maintains 100% code coverage across all new code.

## Code Quality

All code must pass quality checks before merging.

### Type Checking (mypy strict mode)
```bash
make typecheck
```

All code uses `strict = true` in mypy configuration. Type hints are required.

### Linting (ruff)
```bash
make lint
```

Ruff checks for:
- Error codes (E)
- Logical errors (F)
- Import sorting (I)

Line length limit: 100 characters

### Formatting

#### Check formatting without applying changes:
```bash
make lint
```

#### Apply formatting:
```bash
make format
```

This runs both `ruff format` and `black` to ensure consistent formatting.

## Project Structure

```
rag_control/
├── core/                  # Engine and execution logic
├── adapters/              # Integration adapters (LLM, embeddings, vector stores)
├── models/                # Data models and schemas
├── governance/            # Policy and governance logic
├── policy/                # Policy evaluation
├── filter/                # Request/response filtering
├── exceptions/            # Custom exception types
├── observability/         # Logging, tracing, and metrics
│   ├── audit_logger.py   # Audit logging
│   ├── tracing.py        # Distributed tracing
│   └── metrics.py        # Metrics collection (18 metrics)
├── prompt/                # Prompt management
└── spec/                  # Contract specifications
    ├── execution_contract.md
    ├── metrics_contract.md
    ├── tracing_contract.md
    ├── audit_log_contract.md
    └── ...

tests/
├── unit/                  # Unit tests for individual components
├── e2e/                   # End-to-end integration tests
└── fixtures/              # Shared test fixtures
```

## Key Modules

### Observability

The project provides three key observability patterns:

#### 1. Audit Logging
Logs all requests and decisions for compliance and debugging.

#### 2. Distributed Tracing
Records execution flow with OpenTelemetry support. Custom spans added at critical decision points.

#### 3. Metrics (18 total)
- **Request & Latency**: Tracks request throughput and execution duration
- **Stage Performance**: Records duration for each execution stage
- **Retrieval**: Document counts and scores
- **LLM**: Token usage and efficiency
- **Policy**: Policy resolution tracking
- **Errors**: Error types and categories
- **Governance**: Denied request tracking

**Implementations:**
- `NoOpMetricsRecorder` - No-op for production when metrics disabled
- `StructlogMetricsRecorder` - Logs metrics to structlog
- `OpenTelemetryMetricsRecorder` - Full OTel metrics with instrumentation

## Testing Guidelines

### Test Organization

- **Unit tests**: `tests/unit/` - Test individual components in isolation
- **E2E tests**: `tests/e2e/` - Integration tests with full system
- **Fixtures**: `tests/fixtures/` - Shared test data and utilities

### Writing Tests

1. **Use pytest fixtures** for setup/teardown and shared test data
2. **Mock external dependencies** (LLM adapters, vector stores, etc.) in unit tests
3. **Use real implementations** in e2e tests
4. **Test error cases** - Include tests for exceptions and error handling
5. **Aim for 100% coverage** - Use `make coverage` to verify

### Example Test Structure

```python
import pytest
from rag_control.core.engine import Engine
from tests.fixtures import create_mock_adapter

def test_engine_execution():
    """Test basic engine execution."""
    engine = Engine(...)
    result = engine.execute(...)
    assert result.status == "ok"

@pytest.mark.parametrize("input,expected", [
    ("test1", "expected1"),
    ("test2", "expected2"),
])
def test_multiple_cases(input, expected):
    """Test multiple scenarios."""
    assert process(input) == expected
```

## Contributing

### Before Submitting a PR

1. **Run all tests**: `make test`
2. **Check coverage**: `make coverage` (must maintain 100%)
3. **Type check**: `make typecheck`
4. **Lint**: `make lint`
5. **Format**: `make format`

### Full Quality Check

Run all checks in sequence:
```bash
make install-dev && \
make format && \
make typecheck && \
make lint && \
make test && \
make coverage
```

### Branch Strategy

- Base your work on `main`
- Use descriptive branch names (e.g., `feat/add-policy-eval`, `fix/metrics-edge-case`)
- Keep commits atomic and well-described

### Code Guidelines

- **Type hints**: Required on all functions and variables (mypy strict mode)
- **Docstrings**: Required on public modules, classes, and functions
- **Error handling**: Use custom exceptions from `rag_control.exceptions`
- **Logging**: Use structlog for structured logging
- **Comments**: Only for non-obvious logic; code should be self-documenting

### Exception Handling Pattern

The project uses a protocol-based design with exception-swallowing for resilience:

```python
class Adapter(Protocol):
    def execute(self, request: Request) -> Response:
        """Execute adapter logic."""
        ...

# Implementations catch and log exceptions to prevent cascading failures
class SafeAdapter:
    def execute(self, request: Request) -> Response:
        try:
            return self._do_execute(request)
        except Exception as e:
            logger.exception("Adapter failed", error=e)
            # Handle gracefully or raise custom exception
            raise
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Remove and recreate
make clean
make venv
make install-dev
```

### Import Errors
```bash
# Ensure venv is activated
source .venv/bin/activate

# Reinstall dependencies
make install-dev
```

### Type Checking Failures
- Ensure all functions have return type hints
- Import types from `typing` module
- Use Protocol for interface definitions
- Run `make typecheck` to see all issues

### Test Failures
- Run with verbose output: `make test` (already verbose)
- Run specific test: `pytest tests/unit/test_metrics.py -v`
- Check for mock setup issues in fixtures

## Additional Resources

- **Spec Documentation**: See `rag_control/spec/` for detailed contracts
- **Examples**: See `examples/` directory for usage examples
- **License**: See `LICENSE` for RetrievalLabs Business-Restricted License terms

## Getting Help

For questions about development:
1. Check the spec documentation in `rag_control/spec/`
2. Review similar implementations in the codebase
3. Examine existing tests for patterns and examples
4. Check recent commits and PRs for context on decisions
