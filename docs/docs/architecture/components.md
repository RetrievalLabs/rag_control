---
title: Core Components
description: Understanding rag_control core components
---

# Core Components

This document describes the core components that make up rag_control.

## Component Overview

```
┌─────────────────────────────────────────────────────┐
│              RAGControl Engine                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │       Execution Orchestrator                │  │
│  │  - Coordinates all stages                   │  │
│  │  - Manages request lifecycle                │  │
│  │  - Error handling                           │  │
│  └─────────────────────────────────────────────┘  │
│                      ↓                             │
│  ┌──────────────────────────────────────────────┐ │
│  │          Policy Registry                     │ │
│  │  - Policy definitions                        │ │
│  │  - Generation parameters                     │ │
│  │  - Enforcement rules                         │ │
│  └──────────────────────────────────────────────┘ │
│                      ↓                             │
│  ┌──────────────────────────────────────────────┐ │
│  │         Governance Registry                  │ │
│  │  - Organization configurations               │ │
│  │  - Policy rules & conditions                 │ │
│  │  - Policy resolution logic                   │ │
│  └──────────────────────────────────────────────┘ │
│                      ↓                             │
│  ┌──────────────────────────────────────────────┐ │
│  │          Filter Registry                     │ │
│  │  - Filter definitions                        │ │
│  │  - Filter evaluation logic                   │ │
│  │  - Metadata matching                         │ │
│  └──────────────────────────────────────────────┘ │
│                      ↓                             │
│  ┌──────────────────────────────────────────────┐ │
│  │         Adapter Managers                     │ │
│  │  - LLM Adapter                               │ │
│  │  - Query Embedding Adapter                   │ │
│  │  - Vector Store Adapter                      │ │
│  └──────────────────────────────────────────────┘ │
│                      ↓                             │
│  ┌──────────────────────────────────────────────┐ │
│  │       Observability Layer                    │ │
│  │  - Audit Logger                              │ │
│  │  - Tracer                                    │ │
│  │  - Metrics Recorder                          │ │
│  └──────────────────────────────────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## RAGControl Engine

The main orchestrator that coordinates request execution.

### Responsibilities

- Request validation and parsing
- Stage orchestration
- Error handling and recovery
- Result formatting

### Interface

```python
class RAGControl:
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
        """Initialize RAG engine with adapters and config."""

    def run(
        self,
        query: str,
        user_context: UserContext,
    ) -> ExecutionResult:
        """Execute query and return result."""

    def stream(
        self,
        query: str,
        user_context: UserContext,
    ) -> StreamingResult:
        """Stream query response."""
```

## Policy Registry

Manages policy definitions and resolution.

### Responsibilities

- Load and validate policies from config
- Retrieve policy by name
- Validate policy parameters
- Support policy lookup by ID

### Key Operations

```python
class PolicyRegistry:
    def get_policy(self, policy_name: str) -> Policy:
        """Get policy by name."""

    def validate_policy(self, policy: Policy) -> bool:
        """Validate policy configuration."""

    def get_all_policies(self) -> list[Policy]:
        """Get all configured policies."""
```

## Governance Registry

Manages organization configurations and policy resolution rules.

### Responsibilities

- Load and validate organization configs
- Manage policy resolution rules
- Evaluate conditional rules
- Determine applicable policy

### Key Operations

```python
class GovernanceRegistry:
    def get_organization(self, org_id: str) -> Organization:
        """Get organization by ID."""

    def get_policy_rules(self, org_id: str) -> list[PolicyRule]:
        """Get policy rules for organization."""

    def resolve_policy(
        self,
        org_id: str,
        user_context: UserContext,
        documents: list[Document],
    ) -> ResolvedPolicy:
        """Resolve which policy applies."""

    def get_default_policy(self, org_id: str) -> str:
        """Get default policy for organization."""
```

## Filter Registry

Manages filter definitions and evaluation.

### Responsibilities

- Load and validate filters from config
- Evaluate filter conditions
- Support filter matching on documents
- Support filter matching on user context

### Key Operations

```python
class FilterRegistry:
    def get_filter(self, filter_name: str) -> Filter:
        """Get filter by name."""

    def apply_filters(
        self,
        documents: list[Document],
        filters: list[str],
        user_context: UserContext,
    ) -> list[Document]:
        """Apply filters to documents."""

    def validate_filters(
        self,
        filter_names: list[str],
    ) -> bool:
        """Validate filter references."""
```

## Adapter Managers

Wrapper managers for each adapter type.

### LLM Adapter Manager

```python
class LLMAdapterManager:
    def generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        mode: str = "run",
    ) -> GeneratedResponse:
        """Generate response."""

    def stream(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Generator[GeneratedResponse, None, None]:
        """Stream response."""
```

### Query Embedding Adapter Manager

```python
class QueryEmbeddingAdapterManager:
    def embed(self, query: str) -> list[float]:
        """Embed query."""

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
```

### Vector Store Adapter Manager

```python
class VectorStoreAdapterManager:
    def search(
        self,
        embedding: list[float],
        top_k: int,
        org_id: str | None = None,
    ) -> list[RetrievedDocument]:
        """Search documents."""
```

## Observability Layer

Provides audit logging, distributed tracing, and metrics.

### Audit Logger

```python
class AuditLogger:
    def log_request(self, request_id: str, query: str, user_context: UserContext):
        """Log incoming request."""

    def log_decision(self, request_id: str, decision: str, reason: str):
        """Log policy decision."""

    def log_error(self, request_id: str, error: Exception):
        """Log error."""
```

### Tracer

```python
class Tracer:
    def create_request_span(self, request_id: str) -> Span:
        """Create root request span."""

    def create_stage_span(self, parent: Span, stage_name: str) -> Span:
        """Create span for stage."""

    def record_attribute(self, span: Span, key: str, value):
        """Record span attribute."""
```

### Metrics Recorder

```python
class MetricsRecorder:
    def record_request(self, mode: str):
        """Increment request counter."""

    def record_latency(self, stage: str, duration_ms: float):
        """Record stage latency."""

    def record_tokens(self, token_count: int):
        """Record token usage."""

    def record_error(self, error_type: str, error_category: str):
        """Record error metrics."""
```

## Component Interaction

### Request Flow Through Components

```
1. Engine receives request
   ↓
2. Engine calls GovernanceRegistry
   ├─ Resolve organization
   ├─ Resolve applicable policy
   └─ Get org-specific filters
   ↓
3. Engine calls FilterRegistry
   └─ Apply filters to retrieval parameters
   ↓
4. Engine calls QueryEmbeddingAdapterManager
   └─ Embed query
   ↓
5. Engine calls VectorStoreAdapterManager
   └─ Retrieve documents
   ↓
6. Engine calls PolicyRegistry (via GovernanceRegistry)
   └─ Load selected policy
   ↓
7. Engine builds prompt
   ↓
8. Engine calls LLMAdapterManager
   └─ Generate response with policy params
   ↓
9. Engine enforces policy constraints
   ↓
10. Engine calls ObservabilityLayer
    ├─ Log audit events
    ├─ Record traces
    └─ Record metrics
    ↓
11. Engine returns result
```

## Configuration Loading

Components load configuration at initialization:

```python
class ConfigLoader:
    def load(self, config_path: str) -> Config:
        """Load and validate configuration."""

    def validate(self, config: Config) -> bool:
        """Validate configuration structure."""
```

Configuration includes:

- Policies
- Organizations
- Policy rules
- Filters
- Adapter configurations

## Error Handling Strategy

Components use exception-swallowing pattern:

```python
try:
    result = component.execute()
except Exception as e:
    logger.error(f"Component error: {e}")
    # Convert to graceful error response
    return ErrorResponse(error=str(e))
```

This ensures component failures don't crash the engine.

## Extensibility

Components can be extended or replaced:

```python
# Use custom policy registry
class CustomPolicyRegistry(PolicyRegistry):
    def get_policy(self, policy_name: str) -> Policy:
        # Custom logic
        pass

engine = RAGControl(
    llm=llm_adapter,
    query_embedding=embedding_adapter,
    vector_store=vector_store_adapter,
    config_path="config.yaml",
    policy_registry=CustomPolicyRegistry(),
)
```

## See Also

- [Architecture Overview](/architecture/overview)
- [Execution Flow](/architecture/execution-flow)
- [API Reference](/api/engine)
