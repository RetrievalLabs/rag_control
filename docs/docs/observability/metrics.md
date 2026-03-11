---
title: Metrics & Observability
description: Metrics and monitoring for rag_control
---

# Metrics & Observability

rag_control provides comprehensive metrics for observability and monitoring across all request phases.

## Metrics Overview

All metrics are prefixed with `rag_control.` in telemetry output.

![Metrics Dashboard 1](../../../static/img/rag-control-metrics-1.png)

![Metrics Dashboard 2](../../../static/img/rag-control-metrics-2.png)

### Request & Latency Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.requests` | Counter | Total requests processed |
| `rag_control.request.duration_ms` | Histogram | Request latency in milliseconds |

### Stage Tracking

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.stage.duration_ms` | Histogram | Duration of execution stage (org_lookup, embedding, retrieval, policy.resolve, prompt.build, llm.generate, llm.stream, enforcement) |

### Retrieval Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.retrieval.document_count` | Histogram | Number of documents retrieved per request |
| `rag_control.retrieval.document_score` | Histogram | Average document relevance score |
| `rag_control.retrieval.top_document_score` | Histogram | Score of the highest-ranked document |

### Query Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.query.length_chars` | Histogram | Query text length in characters |

### Policy Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.policy.resolved_by_name` | Counter | Count of policy resolutions by policy name |

### LLM Token Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.llm.prompt_tokens` | Counter | Total prompt tokens used |
| `rag_control.llm.completion_tokens` | Counter | Total completion tokens used |
| `rag_control.llm.total_tokens` | Counter | Total tokens (prompt + completion) |
| `rag_control.llm.token_efficiency` | Histogram | Ratio of completion to prompt tokens (completion_tokens / prompt_tokens) |

### Embedding Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.embedding.dimensions` | Histogram | Embedding vector dimensions |

### Enforcement Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.enforcement.violation_count` | Counter | Policy enforcement violations by type (max_output_tokens, missing_citations, invalid_citations, external_knowledge, strict_fallback, unknown) |

### Error Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_control.errors_by_type` | Counter | Error count by exception class name |
| `rag_control.errors_by_category` | Counter | Error count by category (governance, enforcement, embedding, retrieval, llm, policy, other) |
| `rag_control.requests.denied` | Counter | Policy denials (governance, enforcement, or policy category errors only) |

## Metric Labels

### Standard Labels

Most metrics include these labels:

| Label | Values | Description |
|-------|--------|-------------|
| `mode` | `run`, `stream` | Execution mode (streaming vs one-shot) |
| `org_id` | string | Organization ID (empty string if None) |
| `status` | `ok`, `error` | Request outcome |

### Stage Labels

`rag_control.stage.duration_ms` includes:

| Label | Examples |
|-------|----------|
| `stage` | `org_lookup`, `embedding`, `retrieval`, `policy.resolve`, `prompt.build`, `llm.generate`, `llm.stream`, `enforcement` |
| `status` | `ok`, `error` | Stage outcome |

### Model Labels

LLM and embedding metrics include:

| Label | Examples |
|-------|----------|
| `model` | Model identifier (e.g., `gpt-4`, `text-embedding-3-small`) |

### Error Labels

Error metrics include:

| Label | Examples |
|-------|----------|
| `error_type` | Exception class name (e.g., `GovernanceUserContextOrgIDRequiredError`) |
| `error_category` | `governance`, `enforcement`, `embedding`, `retrieval`, `llm`, `policy`, `other` |
| `denial_reason` | `governance`, `enforcement`, `policy` (only for denied requests) |

### Policy Labels

`rag_control.policy.resolved_by_name` includes:

| Label | Examples |
|-------|----------|
| `policy_name` | Policy identifier from configuration |

### Enforcement Labels

`rag_control.enforcement.violation_count` includes:

| Label | Examples |
|-------|----------|
| `policy_name` | Policy identifier from configuration |
| `violation_type` | `max_output_tokens`, `missing_citations`, `invalid_citations`, `external_knowledge`, `strict_fallback`, `unknown` |

## Metric Collection

### Overview

rag_control uses a protocol-based metrics system that:

- **Guarantees reliability**: Metric recording failures never affect request processing (exceptions are caught and suppressed)
- **Supports multiple exporters**: Implement the `MetricsRecorder` protocol to use any observability backend
- **Provides sensible defaults**: Falls back to structured logging if metrics isn't configured


### Initialize Metrics

To use metrics with rag_control:

```python
from rag_control.observability import StructlogMetricsRecorder
from rag_control import RAGControl

# Initialize metrics recorder
metrics = StructlogMetricsRecorder()

engine = RAGControl(
    llm=llm_adapter,
    query_embedding=embedding_adapter,
    vector_store=vector_store_adapter,
    config_path="policy_config.yaml",
    metrics_recorder=metrics
)
```

### Available Implementations

#### NoOpMetricsRecorder

Discards all metrics (useful for testing):

```python
from rag_control.observability.metrics import NoOpMetricsRecorder

metrics = NoOpMetricsRecorder()
```

#### StructlogMetricsRecorder

Logs metrics as JSON structured logs:

```python
from rag_control.observability.metrics import StructlogMetricsRecorder

metrics = StructlogMetricsRecorder(logger_name="rag_control.metrics")

# Metrics are logged with category="metrics"
```

Metrics are emitted as structured JSON logs that can be:
- Parsed by your log aggregation system
- Exported to Prometheus via a log scraper
- Ingested by Datadog, Splunk, ELK, or other log analysis platforms

#### OpenTelemetryMetricsRecorder

Exports metrics via OpenTelemetry API:

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from rag_control.observability import OpenTelemetryMetricsRecorder

# Setup OpenTelemetry with Prometheus exporter
reader = PrometheusMetricReader()
provider = MeterProvider(metric_readers=[reader])

# Configure global OTel provider
from opentelemetry import metrics as otel_metrics
otel_metrics.set_meter_provider(provider)

# Now rag_control will use OTel
metrics = OpenTelemetryMetricsRecorder()

# Metrics available at http://localhost:8000/metrics
```

Supports any OpenTelemetry exporter:
- Prometheus (Prometheus)
- OTLP (Datadog, New Relic, Grafana Cloud, etc.)
- Jaeger
- Zipkin

### Default Recorder Selection

If you don't specify a `metrics_recorder` when creating `RAGControl`, it automatically selects based on what's configured:

1. **Checks if OpenTelemetry metrics are configured** via `otel_metrics.get_meter_provider()`
2. **Uses `OpenTelemetryMetricsRecorder`** if OpenTelemetry SDK is detected
3. **Falls back to `StructlogMetricsRecorder`** if OpenTelemetry is not configured

This ensures metrics always work: if you've set up OpenTelemetry in your application, rag_control will use it. Otherwise, metrics are recorded as structured JSON logs.

```python
from rag_control.core.engine import RAGControl

# Auto-selects metrics recorder based on environment
engine = RAGControl(
    llm=llm_adapter,
    query_embedding=embedding_adapter,
    vector_store=vector_store_adapter,
    config_path="policy_config.yaml",
    # metrics_recorder omitted - uses default behavior
)
```

**Fallback behavior:**
- If OpenTelemetry is configured globally → `OpenTelemetryMetricsRecorder`
- If OpenTelemetry is not configured → `StructlogMetricsRecorder` (JSON logs)

## Custom Metrics

Extend metrics with custom implementations by implementing the `MetricsRecorder` protocol:

```python
from rag_control.observability import MetricsRecorder

class CustomMetricsRecorder:
    def record(
        self,
        name: str,
        value: float,
        *,
        kind: str = "counter",
        unit: str = "",
        **labels: str,
    ) -> None:
        """Record a metric value with labels.

        Args:
            name: Metric name (e.g., 'rag_control.requests')
            value: Numeric value
            kind: 'counter' or 'histogram'
            unit: Measurement unit (e.g., 'ms', 'token')
            **labels: Key-value pairs for metric attributes
        """
        # Your custom recording logic
        pass

custom_metrics = CustomMetricsRecorder()

engine = RAGControl(
    llm=llm_adapter,
    query_embedding=embedding_adapter,
    vector_store=vector_store_adapter,
    config_path="policy_config.yaml",
    metrics_recorder=custom_metrics
)
```

Exception handling is critical: metrics recording failures must never affect request processing. Wrap implementation in try-except blocks that swallow exceptions.

## See Also

- [Audit Logging](/observability/audit-logging)
- [Distributed Tracing](/observability/distributed-tracing)
- [Prometheus Documentation](https://prometheus.io/)
