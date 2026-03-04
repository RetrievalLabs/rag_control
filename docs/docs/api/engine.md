---
title: Engine API Reference
description: RAGControl Engine API documentation
---

# Engine API Reference

The RAGControl Engine is the main orchestrator for executing RAG requests with governance and policy enforcement.

## RAGControl Class

```python
from rag_control.core.engine import RAGControl
from rag_control.models.user import UserContext

engine = RAGControl(
    llm=llm_adapter,
    query_embedding=embedding_adapter,
    vector_store=vector_store_adapter,
    config_path="policy_config.yaml"
)
```

## Constructor

```python
def __init__(
    self,
    llm: LLMAdapter,
    query_embedding: QueryEmbeddingAdapter,
    vector_store: VectorStoreAdapter,
    config_path: str,
    audit_logger: Optional[AuditLogger] = None,
    tracer: Optional[Tracer] = None,
    metrics_recorder: Optional[MetricsRecorder] = None,
):
    """
    Initialize RAGControl engine.

    Args:
        llm: LLM adapter for generation
        query_embedding: Query embedding adapter
        vector_store: Vector store adapter for retrieval
        config_path: Path to policy configuration file
        audit_logger: Optional audit logger (default: NoOpAuditLogger)
        tracer: Optional distributed tracer (default: NoOpTracer)
        metrics_recorder: Optional metrics recorder (default: NoOpMetricsRecorder)

    Raises:
        ConfigurationError: If configuration is invalid
        FileNotFoundError: If config file not found
    """
```

## Methods

### run()

Execute a query and return a complete response.

```python
def run(
    self,
    query: str,
    user_context: UserContext,
) -> ExecutionResult:
    """
    Execute query with governance and policy enforcement.

    Args:
        query: The user's query
        user_context: User context with org_id, user_id, etc.

    Returns:
        ExecutionResult containing:
        - response: Generated response with content and token count
        - policy_name: Name of policy applied
        - enforcement_passed: Whether enforcement checks passed
        - metadata: Execution metadata (documents, latency, etc.)

    Raises:
        PolicyEnforcementError: If enforcement validation fails
        OrganizationNotFoundError: If organization invalid
        RetrievalError: If document retrieval fails
        LLMError: If LLM generation fails
    """
```

### stream()

Stream a query response for real-time output.

```python
def stream(
    self,
    query: str,
    user_context: UserContext,
) -> StreamingResult:
    """
    Stream query response for real-time output.

    Args:
        query: The user's query
        user_context: User context with org_id, user_id, etc.

    Yields:
        Token chunks as they arrive from LLM

    Returns:
        StreamingResult with final metadata

    Raises:
        PolicyEnforcementError: If enforcement validation fails
        OrganizationNotFoundError: If organization invalid
        RetrievalError: If document retrieval fails
        LLMError: If LLM generation fails
    """
```

## Return Types

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    response: GeneratedResponse
    policy_name: str
    enforcement_passed: bool
    documents: list[RetrievedDocument]
    metadata: ExecutionMetadata
```

### GeneratedResponse

```python
@dataclass
class GeneratedResponse:
    content: str                    # Generated text
    token_count: int               # Total tokens used
    prompt_tokens: int             # Prompt tokens
    completion_tokens: int         # Completion tokens
    stop_reason: str              # Why generation stopped
```

### StreamingResult

```python
class StreamingResult:
    def __iter__(self) -> Iterator[str]:
        """Iterate over response chunks."""

    @property
    def metadata(self) -> ExecutionMetadata:
        """Get execution metadata after streaming completes."""
```

### ExecutionMetadata

```python
@dataclass
class ExecutionMetadata:
    request_id: str
    duration_ms: int
    org_id: str
    user_id: str
    policy_resolved_by: str        # rule name or "default"
    documents_retrieved: int
    tokens_used: int
    enforcement_checks: dict
```

## User Context

```python
@dataclass
class UserContext:
    org_id: str                   # Organization ID (required)
    user_id: str                  # User ID (required)
    org_tier: Optional[str] = None
    role: Optional[str] = None
    # Additional custom fields supported
```

## Exception Hierarchy

```python
class RAGControlException(Exception):
    """Base exception for rag_control."""

class OrganizationError(RAGControlException):
    """Organization-related errors."""

class PolicyError(RAGControlException):
    """Policy-related errors."""

class RetrievalError(RAGControlException):
    """Document retrieval errors."""

class LLMError(RAGControlException):
    """LLM generation errors."""

class PolicyEnforcementError(RAGControlException):
    """Policy enforcement failures."""

class ValidationError(RAGControlException):
    """Input validation errors."""
```

## Usage Examples

### Basic Query

```python
from rag_control.core.engine import RAGControl
from rag_control.models.user import UserContext

# Initialize engine
engine = RAGControl(
    llm=your_llm_adapter,
    query_embedding=your_embedding_adapter,
    vector_store=your_vector_store_adapter,
    config_path="policy_config.yaml"
)

# Create user context
user_context = UserContext(
    org_id="acme_corp",
    user_id="user-123",
    org_tier="enterprise"
)

# Execute query
result = engine.run(
    query="What are the key findings from Q1?",
    user_context=user_context
)

# Process result
print(f"Response: {result.response.content}")
print(f"Policy: {result.policy_name}")
print(f"Enforcement passed: {result.enforcement_passed}")
print(f"Tokens: {result.response.token_count}")
```

### Streaming Response

```python
# Stream response
stream_result = engine.stream(
    query="Summarize the financial impact",
    user_context=user_context
)

# Output as it arrives
for chunk in stream_result:
    print(chunk, end="", flush=True)

# Access final metadata
print(f"\nTokens: {stream_result.metadata.tokens_used}")
print(f"Duration: {stream_result.metadata.duration_ms}ms")
```

### Error Handling

```python
from rag_control.core.engine import (
    RAGControl,
    OrganizationError,
    PolicyEnforcementError,
    RAGControlException
)

try:
    result = engine.run(query, user_context)
except OrganizationError as e:
    # Handle org validation failure
    print(f"Invalid organization: {e}")
except PolicyEnforcementError as e:
    # Handle policy violation
    print(f"Policy enforcement failed: {e}")
except RAGControlException as e:
    # Handle other rag_control errors
    print(f"Error: {e}")
```

## Configuration

Engine behavior is controlled via YAML configuration file:

```yaml
policies:
  # Policy definitions

filters:
  # Filter definitions

orgs:
  # Organization configurations
```

See [Configuration Guide](/getting-started/configuration) for details.

## Best Practices

1. **Reuse Engine Instance**: Create once, reuse for multiple requests
2. **Handle Errors**: Catch and log exceptions appropriately
3. **Set Observability**: Configure audit logging, tracing, and metrics
4. **Monitor Performance**: Track latency and token usage
5. **Version Configuration**: Keep configs in version control

## See Also

- [Core Concepts](/concepts/overview)
- [Quick Start](/getting-started/quick-start)
- [API Reference - Policies](/api/policies)
- [API Reference - Governance](/api/governance)
