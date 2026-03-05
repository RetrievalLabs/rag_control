---
title: Metrics & Observability
description: Metrics and monitoring for rag_control
---

# Metrics & Observability

rag_control provides comprehensive metrics for observability and monitoring across all request phases.

## Metrics Overview

All metrics are prefixed with `rag_control.` in telemetry output.

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
- **Auto-detects OpenTelemetry**: If OTel is configured globally, rag_control uses it automatically
- **Provides sensible defaults**: Falls back to structured logging if OTel isn't configured

### Initialize Metrics

To use metrics with rag_control:

```python
from rag_control.observability.metrics import StructlogMetricsRecorder
from rag_control.core.engine import RAGControl

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
from rag_control.observability.metrics import OpenTelemetryMetricsRecorder

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

If you don't specify a `metrics_recorder` when creating `RAGControl`, it automatically:

1. Checks if OpenTelemetry is configured globally
2. Uses `OpenTelemetryMetricsRecorder` if OTel is available
3. Falls back to `StructlogMetricsRecorder` otherwise

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

## Monitoring Dashboards

### Key Performance Indicators

Create dashboards tracking:

1. **Request Throughput**
   - Requests/second
   - Requests/minute by organization

2. **Latency**
   - p50, p95, p99 request latency
   - Stage latencies (embedding, retrieval, LLM)

3. **Token Usage**
   - Total tokens/day
   - Cost projections
   - Efficiency ratios

4. **Policy Enforcement**
   - Policy decisions by name
   - Denial rate
   - Denial reasons

5. **Error Rates**
   - Error rate % by type
   - Error rate by organization
   - Error recovery rate

### Example Prometheus Queries

```promql
# Request rate
rate(rag_control_requests_total[5m])

# P95 request latency
histogram_quantile(0.95, rag_control_request_duration_ms_bucket)

# Total tokens used per hour
increase(rag_control_llm_total_tokens_total[1h])

# Policy denial rate
rate(rag_control_requests_denied_total[5m])

# Error rate by category
rate(rag_control_errors_by_category_total[5m])

# Average document count retrieved
rate(rag_control_retrieval_document_count_sum[5m]) / rate(rag_control_retrieval_document_count_count[5m])

# Average stage latency
avg(rate(rag_control_stage_duration_ms_sum[5m]) / rate(rag_control_stage_duration_ms_count[5m])) by (stage)

# Token efficiency by model
rate(rag_control_llm_token_efficiency_sum[5m]) / rate(rag_control_llm_token_efficiency_count[5m]) by (model)
```

## Alerting Rules

Recommended alerting rules for Prometheus:

### Request Latency

```yaml
alert: HighRequestLatency
expr: histogram_quantile(0.95, rag_control_request_duration_ms_bucket) > 3000
for: 5m
annotations:
  summary: "P95 request latency > 3000ms"
```

### Error Rate

```yaml
alert: HighErrorRate
expr: rate(rag_control_errors_by_type_total[5m]) > 0.05
for: 5m
annotations:
  summary: "Error rate > 5%"
```

### Token Usage

```yaml
alert: HighTokenUsage
expr: rate(rag_control_llm_total_tokens_total[1h]) > 100000
for: 15m
annotations:
  summary: "Token usage > 100k/hour"
```

### Policy Denials

```yaml
alert: HighDenialRate
expr: rate(rag_control_requests_denied_total[5m]) > 0.1
for: 10m
annotations:
  summary: "Policy denial rate > 10%"
```

## Cost Monitoring

Monitor LLM costs using token metrics:

```python
# Example pricing rates (update with actual rates)
MODELS = {
    "gpt-4": {"prompt": 0.00003, "completion": 0.00006},
    "gpt-3.5-turbo": {"prompt": 0.0000005, "completion": 0.0000015},
}

def estimate_cost(model, prompt_tokens, completion_tokens):
    rates = MODELS.get(model, {"prompt": 0, "completion": 0})
    return (prompt_tokens * rates["prompt"] +
            completion_tokens * rates["completion"])
```

### Cost Queries

```promql
# Daily cost estimate (assuming GPT-4 pricing)
(increase(rag_control_llm_prompt_tokens_total[1d]) * 0.00003 +
 increase(rag_control_llm_completion_tokens_total[1d]) * 0.00006)

# Hourly cost per organization
sum by (org_id) (
  increase(rag_control_llm_prompt_tokens_total[1h]) * 0.00003 +
  increase(rag_control_llm_completion_tokens_total[1h]) * 0.00006
)

# Cost per model
sum by (model) (
  increase(rag_control_llm_prompt_tokens_total[1d]) * 0.00003 +
  increase(rag_control_llm_completion_tokens_total[1d]) * 0.00006
)
```

## Performance Analysis

### Identifying Bottlenecks

```promql
# Average stage latency by stage
avg by (stage) (
  rate(rag_control_stage_duration_ms_sum[5m]) /
  rate(rag_control_stage_duration_ms_count[5m])
)

# Which stages take longest (descending)
sort_desc(
  avg by (stage) (
    rate(rag_control_stage_duration_ms_sum[5m]) /
    rate(rag_control_stage_duration_ms_count[5m])
  )
)

# Stage latency by organization
avg by (org_id, stage) (
  rate(rag_control_stage_duration_ms_sum[5m]) /
  rate(rag_control_stage_duration_ms_count[5m])
)
```

### Token Efficiency

```promql
# Average completion/prompt token ratio
avg (
  rate(rag_control_llm_completion_tokens_total[1h]) /
  rate(rag_control_llm_prompt_tokens_total[1h])
)

# Token efficiency by model (lower = more efficient)
avg by (model) (
  rate(rag_control_llm_token_efficiency_sum[5m]) /
  rate(rag_control_llm_token_efficiency_count[5m])
)
```

### Retrieval Quality

```promql
# Average documents retrieved per request
avg (
  rate(rag_control_retrieval_document_count_sum[5m]) /
  rate(rag_control_retrieval_document_count_count[5m])
)

# Average document relevance score
avg (
  rate(rag_control_retrieval_document_score_sum[5m]) /
  rate(rag_control_retrieval_document_score_count[5m])
)
```

## Compliance Reporting

### Policy Enforcement Coverage

Track the percentage of requests that successfully passed policy enforcement:

```promql
# Percent of requests that completed successfully
(
  increase(rag_control_requests_total{status="ok"}[30d]) /
  increase(rag_control_requests_total[30d])
) * 100

# Percent of requests denied by policy
(
  increase(rag_control_requests_denied_total[30d]) /
  increase(rag_control_requests_total[30d])
) * 100
```

### Denial Tracking

```promql
# Total denials by organization
sum by (org_id) (increase(rag_control_requests_denied_total[30d]))

# Total denials by reason
sum by (denial_reason) (increase(rag_control_requests_denied_total[30d]))

# Denial rate by organization
sum by (org_id) (rate(rag_control_requests_denied_total[30d])) /
sum by (org_id) (rate(rag_control_requests_total[30d]))
```

### Error Tracking

```promql
# Errors by organization
sum by (org_id) (increase(rag_control_errors_by_type_total[30d]))

# Error categorization
sum by (error_category) (increase(rag_control_errors_by_category_total[30d]))
```

### Enforcement Violations

```promql
# Total violations by policy
sum by (policy_name) (increase(rag_control_enforcement_violation_count_total[30d]))

# Violation breakdown by type
sum by (violation_type) (increase(rag_control_enforcement_violation_count_total[30d]))

# Violations per policy and type
sum by (policy_name, violation_type) (increase(rag_control_enforcement_violation_count_total[30d]))

# Most common violation type
topk(1, sum by (violation_type) (increase(rag_control_enforcement_violation_count_total[30d])))
```

## Custom Metrics

Extend metrics with custom implementations by implementing the `MetricsRecorder` protocol:

```python
from rag_control.observability.metrics import MetricsRecorder

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

## Best Practices

1. **Monitor Key Metrics**: Focus on throughput, latency, errors
2. **Set Baselines**: Understand normal behavior
3. **Create Alerts**: Alert on anomalies
4. **Review Regularly**: Weekly/monthly metric reviews
5. **Track Trends**: Monitor for gradual degradation
6. **Cost Control**: Monitor token usage and costs

## See Also

- [Audit Logging](/observability/audit-logging)
- [Distributed Tracing](/observability/distributed-tracing)
- [Prometheus Documentation](https://prometheus.io/)
