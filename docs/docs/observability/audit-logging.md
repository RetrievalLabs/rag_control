---
title: Audit Logging
description: Comprehensive audit logging in rag_control
---

# Audit Logging

rag_control provides comprehensive audit logging for compliance, debugging, and operational visibility.

## Overview

Audit logging tracks the complete lifecycle of every request:

- Request received
- Organization lookup
- Document filtering
- Policy resolution
- LLM generation
- Enforcement decisions
- Response or denial
- Errors and exceptions

## Log Structure

Audit logs are structured events with:

```json
{
  "event": "request.received",
  "request_id": "req-abc123def456",
  "timestamp": "2026-03-04T10:30:00.000Z",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "query": "What are the key findings?",
  "source": "api"
}
```

## Log Events

### Request Events

#### request.received

Logged when a request arrives:

```json
{
  "event": "request.received",
  "request_id": "req-abc123",
  "timestamp": "2026-03-04T10:30:00Z",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "query": "...",
  "mode": "run"
}
```

#### request.completed

Logged when request completes successfully:

```json
{
  "event": "request.completed",
  "request_id": "req-abc123",
  "timestamp": "2026-03-04T10:30:02Z",
  "status": "ok",
  "duration_ms": 1500,
  "token_count": 245
}
```

### Organization Events

#### organization.lookup

Logged during organization validation:

```json
{
  "event": "organization.lookup",
  "request_id": "req-abc123",
  "org_id": "acme_corp",
  "status": "found",
  "timestamp": "2026-03-04T10:30:00.005Z"
}
```

### Retrieval Events

#### document.retrieved

Logged after document retrieval:

```json
{
  "event": "document.retrieved",
  "request_id": "req-abc123",
  "document_count": 5,
  "top_score": 0.92,
  "timestamp": "2026-03-04T10:30:00.500Z"
}
```

### Policy Events

#### policy.resolved

Logged when policy is determined:

```json
{
  "event": "policy.resolved",
  "request_id": "req-abc123",
  "policy_name": "strict_citations",
  "resolved_by": "rule:enterprise_strict",
  "timestamp": "2026-03-04T10:30:00.750Z"
}
```

### Enforcement Events

#### enforcement.passed

Logged when enforcement succeeds:

```json
{
  "event": "enforcement.passed",
  "request_id": "req-abc123",
  "enforcement_type": "citations",
  "timestamp": "2026-03-04T10:30:02Z"
}
```

#### enforcement.failed

Logged when enforcement fails:

```json
{
  "event": "enforcement.failed",
  "request_id": "req-abc123",
  "enforcement_type": "citations",
  "reason": "Missing citations for claim: 'X'",
  "timestamp": "2026-03-04T10:30:02Z"
}
```

### Denial Events

#### request.denied

Logged when request is denied:

```json
{
  "event": "request.denied",
  "request_id": "req-abc123",
  "reason": "enforcement_failed",
  "denial_type": "policy_violation",
  "details": "Citation validation failed",
  "timestamp": "2026-03-04T10:30:02Z"
}
```

### Error Events

#### error.occurred

Logged when errors occur:

```json
{
  "event": "error.occurred",
  "request_id": "req-abc123",
  "error_type": "RetrievalError",
  "error_message": "Vector store connection failed",
  "stage": "retrieval",
  "timestamp": "2026-03-04T10:30:00.500Z"
}
```

## Audit Log Levels

Policies define audit logging levels:

### full

Log all events:

```yaml
logging:
  level: full
```

Events logged:
- All request events
- All policy decisions
- All enforcement results
- All errors

### minimal

Log only critical events:

```yaml
logging:
  level: minimal
```

Events logged:
- Request received/completed
- Policy decision
- Denial/error only

### none

Don't log (not recommended):

```yaml
logging:
  level: none
```

## Accessing Audit Logs

### Using the AuditLogger

```python
from rag_control.observability.audit_logger import AuditLogger, StructlogAuditLogger

# Initialize audit logger
audit_logger = StructlogAuditLogger()

# Logs are automatically emitted during engine execution
result = engine.run(query, user_context)
```

### Log Destinations

Logs are sent to:

1. **Structured Logger** (structlog)
   - Console output
   - File output
   - System logging

2. **Log Aggregation** (optional)
   - Elasticsearch
   - CloudWatch
   - Datadog
   - Splunk

### Querying Logs

Example: Find all policy denials for an organization

```python
# Using Python logging
import logging

logger = logging.getLogger('rag_control')

for record in logger.handlers[0].buffer:
    if record.event == 'request.denied' and record.org_id == 'acme_corp':
        print(f"Denied: {record.reason}")
```

## Compliance & Retention

### Compliance Use Cases

Audit logs support:

- **Regulatory Compliance**: HIPAA, GDPR, SOC2
- **Incident Investigation**: Trace what happened and why
- **Access Audits**: Who accessed what, when, why
- **Policy Audits**: Were policies enforced correctly?

### Retention Policy

Recommended retention:

- **Hot Storage** (7 days): Full detail
- **Warm Storage** (90 days): Summarized events
- **Cold Storage** (2+ years): Archived for compliance

## Log Privacy

### Sensitive Data

By default, audit logs don't include:

- Actual query content (can be enabled)
- Response content
- Document content
- User credentials

Can be enabled via configuration:

```yaml
logging:
  include_query: true      # Include query text
  include_response: false  # Exclude response
  include_documents: false # Exclude document content
```

## Performance Impact

Audit logging has minimal performance impact:

- Structured logging is asynchronous
- Non-blocking by default
- `<5ms` overhead per request

## Best Practices

1. **Always Enable Logging**: For compliance and debugging
2. **Use Structured Format**: Easier to parse and aggregate
3. **Set Appropriate Levels**: Balance detail vs. storage
4. **Archive Logs**: Keep long-term audit trail
5. **Monitor Logs**: Alert on errors and denials
6. **Protect Logs**: Restrict access to audit data

## Integration Examples

### With Datadog

```python
from rag_control.observability.audit_logger import DatadogAuditLogger

audit_logger = DatadogAuditLogger(
    api_key="your-api-key",
    service="rag-control"
)

engine = RAGControl(
    # ... other params
    audit_logger=audit_logger
)
```

### With CloudWatch

```python
from rag_control.observability.audit_logger import CloudWatchAuditLogger

audit_logger = CloudWatchAuditLogger(
    log_group="/aws/rag-control",
    log_stream="requests"
)

engine = RAGControl(
    # ... other params
    audit_logger=audit_logger
)
```

## See Also

- [Audit Log Contract](/specs/audit-log-contract)
- [Distributed Tracing](/observability/distributed-tracing)
- [Metrics](/observability/metrics)
