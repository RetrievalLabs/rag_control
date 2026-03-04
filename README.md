# rag_control

A runtime governance, security, and execution control layer for Retrieval-Augmented Generation (RAG) systems.

**rag_control** provides enterprise-grade policy enforcement, security governance, and observability for RAG applications. Control what your RAG system retrieves, how it generates responses, and enforce compliance policies at runtime.

## Overview

RAG systems are powerful but can be risky in production:
- **Hallucinations**: LLMs may generate content not grounded in retrieved documents
- **Data Leakage**: Sensitive information might be retrieved or exposed
- **Compliance**: Regulations require audit trails and enforcement controls
- **Cost**: Token usage and retrieval operations need optimization

**rag_control** addresses these challenges with:

- **Policy-Based Generation**: Define and enforce generation policies (temperature, output length, citation requirements, external knowledge restrictions)
- **Runtime Enforcement**: Validate responses against policies before returning them to users
- **Governance & Security**: Apply organization-level rules, role-based access control, and data classification filters
- **Comprehensive Audit Logging**: Track all requests, decisions, and denials for compliance
- **Distributed Tracing**: Understand execution flow and identify performance bottlenecks
- **Metrics & Observability**: 18+ metrics covering throughput, latency, quality, costs, and errors

## Key Features

### 🛡️ Policy Enforcement
- Define multiple policies with different strictness levels
- Control temperature, max output tokens, reasoning depth
- Enforce citation requirements and validation
- Prevent external knowledge generation
- Apply context-aware fallback strategies

### 🔐 Governance & Security
- Organization-level access control
- Retrieval filtering by data classification and metadata
- User context validation
- Policy resolution based on org rules and data sensitivity

### 📊 Observability
- **Audit Logging**: Full request/response lifecycle tracking
- **Distributed Tracing**: OpenTelemetry integration for flow analysis
- **Metrics**: Token usage, latency, error rates, policy decisions

### 🚀 Production Ready
- Exception-swallowing pattern ensures governance failures never break request flow
- Comprehensive error handling with custom exception types
- Type-safe with mypy strict mode compliance
- 100% code coverage with extensive test suite

## Installation

```bash
pip install rag_control
```

### Requirements
- Python 3.9+
- Dependencies: `pydantic`, `pyyaml`, `structlog`, `opentelemetry-api`, `opentelemetry-sdk`

## Quick Start

### 1. Define Policies

Create a `policy_config.yaml`:

```yaml
policies:
  - name: strict_citations
    description: Strict policy with citation enforcement
    generation:
      reasoning_level: limited
      allow_external_knowledge: false
      require_citations: true
      temperature: 0.0
      max_output_tokens: 512
    enforcement:
      validate_citations: true
      block_on_missing_citations: true
      prevent_external_knowledge: true
    logging:
      level: full

  - name: soft_research
    description: Relaxed policy for exploratory research
    generation:
      reasoning_level: full
      allow_external_knowledge: false
      require_citations: true
      temperature: 0.1
      max_output_tokens: 1024
    enforcement:
      validate_citations: true
      block_on_missing_citations: false
      prevent_external_knowledge: true
    logging:
      level: full

filters:
  - name: enterprise_only
    condition:
      field: org_tier
      operator: equals
      value: enterprise
      source: user
```

### 2. Initialize the Engine

```python
from rag_control.core.engine import RAGControl
from rag_control.models.user import UserContext

# Initialize with your adapters and config
engine = RAGControl(
    llm=your_llm_adapter,
    query_embedding=your_embedding_adapter,
    vector_store=your_vector_store_adapter,
    config_path="policy_config.yaml"
)

# Create user context
user_context = UserContext(
    org_id="acme-corp",
    user_id="user-123",
    org_tier="enterprise"
)
```

### 3. Run Queries

```python
# Execute a query with governance and policy enforcement
result = engine.run(
    query="What are the key findings from our Q1 report?",
    user_context=user_context
)

print(f"Policy applied: {result.policy_name}")
print(f"Enforcement passed: {result.enforcement_passed}")
print(f"Response: {result.response.content}")
print(f"Tokens used: {result.response.token_count}")

# Or stream responses
stream_result = engine.stream(
    query="Summarize the financial impact...",
    user_context=user_context
)

for chunk in stream_result.response:
    print(chunk.content, end="", flush=True)
```

## Architecture

### Core Components

- **Engine**: Orchestrates the RAG execution pipeline with governance and policy enforcement
- **Policy Registry**: Manages generation and enforcement policies
- **Governance Registry**: Applies organization-level rules and access control
- **Filter Registry**: Manages data classification and retrieval filters
- **Adapters**: Pluggable interfaces for LLMs, embeddings, and vector stores

### Execution Flow

```
1. Validate org identity from user context
   ↓
2. Resolve org and apply retrieval filters
   ↓
3. Embed query
   ↓
4. Retrieve documents with org-level top_k
   ↓
5. Resolve policy via governance rules
   ↓
6. Build prompt with policy context
   ↓
7. Call LLM with policy-controlled parameters
   ↓
8. Apply enforcement checks (citations, knowledge, etc.)
   ↓
9. Emit audit events and traces
   ↓
10. Return response or raise policy violation
```

## Observability

### Audit Logging

Every request generates audit events:
```python
{
    "event": "request.received",
    "request_id": "req-abc123",
    "org_id": "acme-corp",
    "user_id": "user-123",
    "timestamp": "2026-03-04T10:30:00Z"
}
```

### Distributed Tracing

OpenTelemetry integration tracks execution stages:
```
request_span
├── org_lookup_span
├── embedding_span
├── retrieval_span
├── policy_resolution_span
├── llm_generation_span
└── enforcement_span
```

### Metrics (18 total)

- **Throughput**: Request count, throughput per second
- **Latency**: Request duration, stage durations
- **Quality**: Retrieved document scores, top-k metrics
- **LLM**: Token counts, efficiency ratios
- **Errors**: Error types, error categories, denial reasons
- **Custom**: Policy resolutions, embedding dimensions

## Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)**: Development setup, testing, quality standards
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Contribution guidelines
- **[Execution Contract](rag_control/spec/execution_contract.md)**: Engine behavior specification
- **[Audit Log Contract](rag_control/spec/audit_log_contract.md)**: Audit logging specification
- **[Metrics Contract](rag_control/spec/metrics_contract.md)**: Metrics specification
- **[Tracing Contract](rag_control/spec/tracing_contract.md)**: Tracing specification
- **[Control Plane Config Contract](rag_control/spec/control_plane_config_contract.md)**: Configuration specification

## Examples

See the `examples/` directory for:
- `policy_config.yaml`: Complete policy configuration example

## Security

- Exception-swallowing pattern ensures governance failures are handled gracefully
- All external inputs validated with Pydantic
- Type-safe with strict mypy enforcement
- Regular security audits and dependency updates

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines:
- **Issues**: Anyone can open issues, bugs, and feature requests
- **Pull Requests**: RetrievalLabs team members only
- **Code Standards**: 100% coverage, type checking, formatting compliance required

## Support

- Check [DEVELOPMENT.md](DEVELOPMENT.md) for setup issues
- Review spec documentation in `rag_control/spec/` for detailed contracts
- Open an issue for bugs and feature requests

## License

This project is licensed under the **RetrievalLabs Business-Restricted License (RBRL)**.

- **Personal/Non-Commercial Use**: Permitted
- **Business/Commercial Use**: Prohibited without a written contract with RetrievalLabs Co.
- **Modifications/Derivative Works**: Prohibited without a written contract with RetrievalLabs Co.

See [LICENSE](LICENSE) for full terms.

---

**Built by [RetrievalLabs](https://retrievallabs.com)** — Enterprise RAG Governance and Security
