---
title: Testing Guide
description: Testing standards and practices for rag_control
---

# Testing Guide

## Test Structure

Tests are organized by type:

```
tests/
├── unit/              # Unit tests
│   ├── test_engine.py
│   ├── test_policies.py
│   ├── test_governance.py
│   └── ...
├── integration/       # Integration tests
│   ├── test_execution_flow.py
│   └── ...
└── e2e/              # End-to-end tests
    ├── test_full_flow.py
    └── ...
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/unit/test_engine.py
```

### Run Specific Test Function

```bash
pytest tests/unit/test_engine.py::test_engine_initialization
```

### Run with Coverage

```bash
pytest --cov=rag_control --cov-report=html
```

### Run with Verbose Output

```bash
pytest -v
```

## Test Requirements

### Coverage

- **Minimum**: 80%
- **Target**: 100% on critical paths
- **Enforcement**: CI blocks PRs with `<80%` coverage

### Test Types

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test complete flows

### Mock Objects

Use mocks for external dependencies:

```python
from unittest.mock import Mock, patch

def test_with_mock():
    mock_llm = Mock()
    mock_llm.generate.return_value = GeneratedResponse(
        content="response",
        token_count=10,
        stop_reason="end_turn"
    )
    # Test using mock_llm
```

## Writing Tests

### Test Template

```python
import pytest
from rag_control.core.engine import RAGControl

def test_engine_executes_request():
    # Arrange
    engine = RAGControl(
        llm=mock_llm,
        query_embedding=mock_embedding,
        vector_store=mock_vector_store,
        config_path="test_config.yaml"
    )
    user_context = UserContext(
        org_id="test_org",
        user_id="test_user"
    )

    # Act
    result = engine.run("test query", user_context)

    # Assert
    assert result.enforcement_passed
    assert result.response.content is not None
```

### Using Fixtures

```python
@pytest.fixture
def engine():
    return RAGControl(
        llm=mock_llm,
        query_embedding=mock_embedding,
        vector_store=mock_vector_store,
        config_path="test_config.yaml"
    )

def test_with_fixture(engine):
    result = engine.run("query", UserContext(...))
    assert result is not None
```

## Test Configuration

Create `test_config.yaml` for tests:

```yaml
policies:
  - name: test_policy
    generation:
      reasoning_level: limited
      allow_external_knowledge: false
      require_citations: false
      temperature: 0.0
      max_output_tokens: 512
    enforcement:
      validate_citations: false
      block_on_missing_citations: false
      prevent_external_knowledge: false
    logging:
      level: minimal

orgs:
  - org_id: test_org
    default_policy: test_policy
    document_policy:
      top_k: 5
```

## Quality Standards

### Code Coverage

```bash
# Check coverage
pytest --cov=rag_control --cov-report=term-missing

# Generate HTML report
pytest --cov=rag_control --cov-report=html
# Open htmlcov/index.html
```

### Type Checking

```bash
# Strict type checking
mypy --strict rag_control
```

### Linting

```bash
# Check lint
ruff check rag_control

# Auto-fix issues
ruff check --fix rag_control
```

### Formatting

```bash
# Check formatting
black --check rag_control

# Format code
black rag_control
```

## Continuous Integration

Tests run on every PR with:

- ✅ Unit tests (pytest)
- ✅ Integration tests (pytest)
- ✅ Coverage check (80%+ required)
- ✅ Type checking (mypy strict)
- ✅ Linting (ruff)
- ✅ Formatting (black)

## Common Issues

### Import Errors

Ensure you're running tests from repo root:

```bash
cd /path/to/rag_control
pytest
```

### Mock Not Working

Patch at the point of use:

```python
# Wrong - patches wrong location
with patch('openai.ChatCompletion'):

# Correct - patches where used
with patch('rag_control.adapters.openai.ChatCompletion'):
```

### Async Tests

For async code:

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await engine.run_async(query)
    assert result is not None
```

## Performance Testing

For performance-critical code:

```python
import pytest

@pytest.mark.performance
def test_embedding_latency():
    # Should complete in <1 second
    start = time.time()
    embedding = adapter.embed("test query")
    duration = time.time() - start
    assert duration < 1.0
```

## See Also

- [Development Setup](/development/setup)
- [Contributing Guide](/development/contributing)
- [GitHub Tests](https://github.com/RetrievalLabs/rag_control/tree/main/tests)
