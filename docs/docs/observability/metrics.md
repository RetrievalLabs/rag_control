---
title: Metrics & Observability
description: Metrics and monitoring for rag_control
---

# Metrics & Observability

rag_control provides 18+ metrics for comprehensive observability and monitoring.

## Metrics Overview

### Request & Latency Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `requests` | Counter | Total requests processed |
| `request.duration_ms` | Histogram | Request latency in milliseconds |

### Stage Tracking

| Metric | Type | Description |
|--------|------|-------------|
| `stage.duration_ms` | Histogram | Duration of execution stage (org_lookup, embedding, retrieval, etc.) |

### Retrieval Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `document_count` | Histogram | Number of documents retrieved per request |
| `document_score` | Histogram | Individual document relevance scores |
| `top_document_score` | Histogram | Score of top-ranked document |

### Query Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `query.length_chars` | Histogram | Query text length in characters |

### Policy Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `policy.resolved_by_name` | Counter | Count of decisions by policy name |

### LLM Token Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `prompt_tokens` | Counter | Total prompt tokens used |
| `completion_tokens` | Counter | Total completion tokens used |
| `total_tokens` | Counter | Total tokens used (prompt + completion) |
| `token_efficiency` | Histogram | Ratio of completion to prompt tokens |

### Embedding Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `embedding.dimensions` | Histogram | Embedding vector dimensions |

### Error Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `errors_by_type` | Counter | Error count by exception type |
| `errors_by_category` | Counter | Error count by category (governance, embedding, retrieval, llm, policy, other) |
| `requests.denied` | Counter | Policy denials (only for governance/enforcement/policy categories) |

## Metric Labels

All metrics include standard labels:

| Label | Values | Description |
|-------|--------|-------------|
| `mode` | `run`, `stream` | Execution mode |
| `org_id` | string | Organization ID (empty if None) |
| `status` | `ok`, `error` | Request status |

### Stage Labels

`stage.duration_ms` includes:

| Label | Examples |
|-------|----------|
| `stage` | `org_lookup`, `embedding`, `retrieval`, `policy_resolution`, `llm_generation`, `enforcement` |

### Error Labels

Error metrics include:

| Label | Examples |
|-------|----------|
| `error_type` | Exception class name |
| `error_category` | `governance`, `embedding`, `retrieval`, `llm`, `policy`, `other` |
| `denial_reason` | `governance`, `enforcement`, `policy` (subset of error_category) |

## Metric Collection

### Initialize Metrics

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

### Exporters

#### Prometheus

```python
from rag_control.observability.metrics import PrometheusMetricsRecorder

metrics = PrometheusMetricsRecorder(port=8000)

# Metrics available at http://localhost:8000/metrics
```

#### OpenTelemetry

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from rag_control.observability.metrics import OpenTelemetryMetricsRecorder

# Setup OpenTelemetry metrics
reader = PrometheusMetricReader()
provider = MeterProvider(metric_readers=[reader])

metrics = OpenTelemetryMetricsRecorder(provider=provider)
```

#### Datadog

```python
from rag_control.observability.metrics import DatadogMetricsRecorder

metrics = DatadogMetricsRecorder(
    api_key="your-api-key",
    app_key="your-app-key"
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
rate(requests_total[5m])

# P95 latency
histogram_quantile(0.95, request_duration_ms_bucket)

# Total tokens used
increase(total_tokens[1h])

# Policy denial rate
rate(requests_denied_total[5m])

# Error rate by category
rate(errors_by_category[5m])

# Average document count retrieved
rate(document_count_sum[5m]) / rate(document_count_count[5m])
```

## Alerting Rules

Recommended alerting rules:

### Request Latency

```yaml
alert: HighRequestLatency
expr: histogram_quantile(0.95, request_duration_ms_bucket) > 3000
for: 5m
```

### Error Rate

```yaml
alert: HighErrorRate
expr: rate(errors_by_type[5m]) > 0.05
for: 5m
```

### Token Usage

```yaml
alert: HighTokenUsage
expr: rate(total_tokens[1h]) > 100000
for: 15m
```

### Policy Denials

```yaml
alert: HighDenialRate
expr: rate(requests_denied[5m]) > 0.1
for: 10m
```

## Cost Monitoring

Monitor LLM costs using token metrics:

```python
# GPT-4 pricing (example)
PROMPT_PRICE = 0.00003  # $ per token
COMPLETION_PRICE = 0.00006  # $ per token

def estimate_cost(prompt_tokens, completion_tokens):
    return (prompt_tokens * PROMPT_PRICE +
            completion_tokens * COMPLETION_PRICE)
```

Queries:

```promql
# Daily cost estimate
(increase(prompt_tokens_total[1d]) * 0.00003 +
 increase(completion_tokens_total[1d]) * 0.00006)

# Cost per organization
sum by (org_id) (
  increase(prompt_tokens_total[1h]) * 0.00003 +
  increase(completion_tokens_total[1h]) * 0.00006
)
```

## Performance Analysis

### Identifying Bottlenecks

```promql
# Stage latencies
rate(stage_duration_ms_sum[5m]) / rate(stage_duration_ms_count[5m])

# Which stages take longest?
sort_desc(
  rate(stage_duration_ms_sum[5m]) / rate(stage_duration_ms_count[5m])
)
```

### Token Efficiency

```promql
# Completion/prompt ratio
rate(completion_tokens[1h]) / rate(prompt_tokens[1h])

# Lower ratio = more efficient
```

## Compliance Reporting

Use metrics for compliance reports:

### Policy Enforcement Coverage

```promql
# Percent of requests with policy enforcement
(
  increase(requests{status="ok"}[30d]) +
  increase(requests_denied[30d])
) / increase(requests[30d]) * 100
```

### Denial Tracking

```promql
# Denials by organization
sum by (org_id) (increase(requests_denied[30d]))

# Denial reasons
sum by (denial_reason) (increase(requests_denied[30d]))
```

## Custom Metrics

Extend with custom metrics:

```python
from rag_control.observability.metrics import MetricsRecorder

class CustomMetricsRecorder(MetricsRecorder):
    def record_custom_metric(self, name, value, labels):
        # Your custom recording logic
        pass

custom_metrics = CustomMetricsRecorder()
```

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
