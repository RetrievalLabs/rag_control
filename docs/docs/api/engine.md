---
title: Engine API Reference
description: RAGControl Engine API and initialization
---

# Engine API Reference

The main orchestrator for executing RAG requests with governance and policy enforcement.

## RAGControl

```python
from rag_control import RAGControl
```

Initialize with adapters and governance configuration.

## Constructor

```python
def __init__(
    self,
    llm: LLM,
    query_embedding: QueryEmbedding,
    vector_store: VectorStore,
    config: ControlPlaneConfig | None = None,
    config_path: str | Path | None = None,
    audit_logger: AuditLogger | None = None,
    tracer: Tracer | None = None,
    metrics_recorder: MetricsRecorder | None = None,
)
```

**Parameters:**
- `llm: LLM` - LLM adapter for generation
- `query_embedding: QueryEmbedding` - Query embedding adapter
- `vector_store: VectorStore` - Vector store adapter for retrieval
- `config: ControlPlaneConfig | None` - Config object (optional, use config_path instead)
- `config_path: str | Path | None` - Path to YAML config file (optional)
- `audit_logger: AuditLogger | None` - Audit logger (default: StructlogAuditLogger)
- `tracer: Tracer | None` - Distributed tracer (default: default tracer)
- `metrics_recorder: MetricsRecorder | None` - Metrics recorder (default: default recorder)

**Note:** Provide exactly one of `config` or `config_path`.

## Methods

### run()

Execute a query synchronously and return a complete response.

`run(query: str, user_context: UserContext) -> RunResponse`

**Returns:** RunResponse with policy name, enforcement result, and LLMResponse

### stream()

Stream a query response for real-time output.

`stream(query: str, user_context: UserContext) -> StreamResponse`

**Returns:** StreamResponse with policy name, enforcement result, and LLMStreamResponse

## Return Types

### RunResponse

- `policy_name: str` - Policy applied
- `org_id: str` - Organization ID
- `user_id: str` - User ID
- `trace_id: str | None` - Trace ID (if tracing enabled)
- `filter_name: str | None` - Filter applied (if any)
- `retrieval_top_k: int` - Number of docs requested
- `retrieved_count: int` - Number of docs retrieved
- `enforcement_passed: bool` - Enforcement check result
- `response: LLMResponse` - Generated response with content, usage, metadata

### StreamResponse

- `policy_name: str` - Policy applied
- `org_id: str` - Organization ID
- `user_id: str` - User ID
- `trace_id: str | None` - Trace ID (if tracing enabled)
- `filter_name: str | None` - Filter applied (if any)
- `retrieval_top_k: int` - Number of docs requested
- `retrieved_count: int` - Number of docs retrieved
- `enforcement_attached: bool` - Enforcement check result
- `response: LLMStreamResponse` - Streaming response with usage, metadata

## UserContext

```python
from rag_control.models import UserContext

context = UserContext(
    org_id="acme-corp",
    user_id="user-123",
)
```

**Fields:**
- `org_id: str` - Organization ID (required)
- `user_id: str` - User ID (required)
- Additional custom fields supported

## Execution Flow

1. **Organization Lookup** - Validate org_id and retrieve org config
2. **Document Retrieval** - Embed query and retrieve top-k documents
3. **Policy Resolution** - Determine which policy applies based on rules
4. **Prompt Building** - Build LLM prompt with retrieved documents and policy
5. **Generation** - Generate response via LLM adapter
6. **Enforcement** - Validate response against enforcement policy

## Configuration

Pass config programmatically or from YAML:

```python
# From ControlPlaneConfig object
from rag_control.models.config import ControlPlaneConfig

config = ControlPlaneConfig(policies=[...], filters=[...], orgs=[...])
engine = RAGControl(..., config=config)
```

```python
# From YAML file
engine = RAGControl(..., config_path="config.yaml")
```

See [Policy, Governance & Filters API](/api/policy-gov-config) for configuration details.

## Exceptions

Common exceptions from `rag_control.exceptions`:

- `RagControlError` - Base exception
- `GovernanceOrgNotFoundError` - Organization not found
- `GovernancePolicyDeniedError` - Policy denied by governance
- `GovernanceUserContextOrgIDRequiredError` - org_id required
- `EnforcementPolicyViolationError` - Enforcement validation failed
- `AdapterError` - Adapter integration failures

See [Exceptions API](/api/exceptions) for complete reference.

## See Also

- [Adapters API](/api/adapters)
- [Policy, Governance & Filters API](/api/policy-gov-config)
- [Exceptions API](/api/exceptions)
