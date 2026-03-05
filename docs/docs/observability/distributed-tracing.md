---
title: Distributed Tracing
description: Distributed tracing and OpenTelemetry integration
---

# Distributed Tracing

rag_control integrates with OpenTelemetry for distributed tracing, providing visibility into request execution flow and performance bottlenecks.

## Overview

Distributed tracing tracks:

- Complete request lifecycle
- Stage-by-stage execution
- Latency at each stage
- External service calls
- Errors and exceptions

## Span Hierarchy

Requests create a nested span hierarchy:

```
request_span (root)
├── org_lookup_span
├── document_filtering_span
├── embedding_span
│   └── embedding_api_call_span
├── retrieval_span
│   └── vector_store_search_span
├── policy_resolution_span
├── prompt_building_span
├── llm_generation_span
│   └── llm_api_call_span
├── enforcement_span
└── observability_span
```

## Span Attributes

Each span includes relevant attributes:

### Root Request Span

```
request_span
├── request_id: "req-abc123"
├── org_id: "acme_corp"
├── user_id: "user-123"
├── query: "What are findings?"
├── mode: "run"
├── status: "ok" | "error"
└── duration_ms: 1500
```

### Organization Lookup Span

```
org_lookup_span
├── org_id: "acme_corp"
├── status: "found" | "not_found"
└── duration_ms: 2
```

### Document Filtering Span

```
document_filtering_span
├── filter_count: 2
├── filters_applied: ["enterprise_only", "internal_only"]
└── duration_ms: 5
```

### Query Embedding Span

```
embedding_span
├── query_length: 50
├── embedding_dimensions: 1536
└── duration_ms: 350
```

### Document Retrieval Span

```
retrieval_span
├── top_k: 5
├── document_count: 5
├── min_score: 0.85
├── max_score: 0.95
└── duration_ms: 75
```

### Policy Resolution Span

```
policy_resolution_span
├── org_id: "acme_corp"
├── policy_name: "strict_citations"
├── resolved_by: "rule:enterprise_strict"
└── duration_ms: 2
```

### LLM Generation Span

```
llm_generation_span
├── policy_name: "strict_citations"
├── temperature: 0.0
├── max_tokens: 512
├── prompt_tokens: 150
├── completion_tokens: 95
├── total_tokens: 245
└── duration_ms: 2000
```

### Enforcement Span

```
enforcement_span
├── enforcement_type: "citations" | "knowledge_restriction"
├── status: "passed" | "failed"
└── duration_ms: 40
```

## Tracing Setup

### Initialize with OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from rag_control.core.engine import RAGControl
from rag_control.observability.tracing import OpenTelemetryTracer

# Setup OpenTelemetry exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

trace_provider = TracerProvider()
trace_provider.add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)
trace.set_tracer_provider(trace_provider)

# Initialize rag_control with tracing
tracer = OpenTelemetryTracer()

engine = RAGControl(
    llm=llm_adapter,
    query_embedding=embedding_adapter,
    vector_store=vector_store_adapter,
    config_path="policy_config.yaml",
    tracer=tracer
)
```

### Exporters

#### Jaeger

```python
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
```

#### Datadog

```python
from opentelemetry.exporter.datadog.propagator import DatadogPropagator
from opentelemetry.exporter.datadog import DatadogSpanExporter

dd_exporter = DatadogSpanExporter(
    agent_host="localhost",
    agent_port=8126,
)
```

#### OTLP (OpenTelemetry Protocol)

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
)
```

## Trace Visualization

### Jaeger UI

Access traces at `http://localhost:16686`:

1. Select "rag-control" service
2. Filter by request_id or org_id
3. View span waterfall diagram

### Viewing a Trace

```
request_span ═══════════════════════════════════════════
├── org_lookup_span ═════[5ms]
├── document_filtering_span ═════[10ms]
├── embedding_span ═════════════════════[350ms]
├── retrieval_span ═══════[75ms]
├── policy_resolution_span ═[2ms]
├── llm_generation_span ═════════════════════[2000ms]
├── enforcement_span ═════════[40ms]
└── observability_span ═══════[18ms]
```

## Trace Correlation

Traces are automatically correlated with:

- **Request ID**: Unique per request
- **User ID**: From user context
- **Organization ID**: From user context
- **Span Context**: OpenTelemetry context propagation

### Cross-Service Correlation

For distributed systems, propagate context:

```python
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.propagators.b3 import B3SingleFormat

# Use Jaeger propagator
propagator = JaegerPropagator()

# Extract context from incoming request
context = propagator.extract(request.headers)

# Context will be used for child spans
result = engine.run(query, user_context)
```

## Trace Sampling

Control trace collection with sampling:

```python
from opentelemetry.sdk.trace.sampling import ProbabilitySampler

# Sample 10% of traces for cost control
sampler = ProbabilitySampler(rate=0.1)

trace_provider = TracerProvider(sampler=sampler)
```

## Performance Impact

Tracing overhead:

- **Enabled**: `<10ms` per request
- **Disabled**: `<1ms` per request

For high-throughput systems, use sampling.

## Debugging with Traces

### Find Slow Requests

Query for requests >2000ms:

```
operation_name="request" AND duration>2000ms
```

### Find Errors

Query for failed requests:

```
operation_name="request" AND status="error"
```

### Trace a Specific Request

```
request_id="req-abc123"
```

## Best Practices

1. **Always Enable Tracing**: Minimal overhead for high value
2. **Use Sampling**: Reduce overhead in production
3. **Correlate Requests**: Use request IDs consistently
4. **Monitor Traces**: Alert on slow requests
5. **Propagate Context**: For distributed systems

## Example Trace Analysis

### Finding Performance Bottlenecks

```
Total latency: 2.5s

Breakdown:
- Embedding: 350ms (14%) - Slow but expected
- LLM generation: 2000ms (80%) - Main cost
- Other stages: 150ms (6%)

Recommendation: LLM is the bottleneck, not rag_control
```

### Identifying Policy Denials

```
request_span
├── policy_resolved_span
│   └── policy: strict_citations
├── llm_generation_span
│   └── status: ok
├── enforcement_span
│   └── status: failed
│       └── reason: missing_citations
└── request_span
    └── status: denied
```

## See Also

- [Audit Logging](/observability/audit-logging)
- [Metrics](/observability/metrics)
- [OpenTelemetry Documentation](https://opentelemetry.io/)
