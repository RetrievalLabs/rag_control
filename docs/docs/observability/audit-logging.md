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

All audit events include these core fields:
- `event`: Event name
- `request_id`: Unique request identifier (UUID)
- `trace_id`: Distributed trace identifier
- `org_id`: Organization identifier
- `user_id`: User identifier
- `mode`: "run" or "stream"
- `component`: "rag_control.engine"
- `sdk_name`: "rag_control"
- `sdk_version`: SDK version
- `company_name`: "RetrievalLabs"
- `level`: Log level (debug, info, warning, error, critical)

### Request Events

#### request.received

Logged when a request arrives:

```json
{
  "event": "request.received",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "sdk_name": "rag_control",
  "sdk_version": "1.0.0",
  "company_name": "RetrievalLabs",
  "level": "info"
}
```

#### request.completed

Logged when request completes successfully:

```json
{
  "event": "request.completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "policy_name": "strict_citations",
  "retrieved_count": 5,
  "retrieved_doc_ids": ["doc-1", "doc-2", "doc-3", "doc-4", "doc-5"],
  "llm_model": "gpt-4",
  "llm_temperature": 0.7,
  "llm_max_output_tokens": 2048,
  "prompt_tokens": 450,
  "completion_tokens": 285,
  "total_tokens": 735,
  "enforcement_passed": true,
  "level": "info"
}
```

#### request.denied

Logged when request is denied during governance or policy checks (not during enforcement):

```json
{
  "event": "request.denied",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": null,
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "error_type": "GovernanceUserContextOrgIDRequiredError",
  "error_message": "Organization ID is required in user context",
  "level": "warning"
}
```

### Organization Events

#### organization.lookup

Logged after organization is successfully resolved:

```json
{
  "event": "organization.lookup",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "status": "found",
  "filter_name": "acme_filter",
  "retrieval_top_k": 5,
  "level": "info"
}
```

### Retrieval Events

#### retrieval.completed

Logged after document retrieval:

```json
{
  "event": "retrieval.completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "retrieved_count": 5,
  "retrieved_doc_ids": ["doc-1", "doc-2", "doc-3", "doc-4", "doc-5"],
  "level": "info"
}
```

### Policy Events

#### policy.resolved

Logged when policy is determined for the request:

```json
{
  "event": "policy.resolved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "policy_name": "strict_citations",
  "level": "info"
}
```

### Enforcement Events

#### enforcement.passed

Logged when enforcement succeeds on a non-streaming request:

```json
{
  "event": "enforcement.passed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "policy_name": "strict_citations",
  "level": "info"
}
```

#### enforcement.attached

Logged when enforcement is attached to a streaming response:

```json
{
  "event": "enforcement.attached",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "stream",
  "component": "rag_control.engine",
  "policy_name": "strict_citations",
  "level": "info"
}
```

## Audit Log Levels

Policies define audit logging levels, which control which events are emitted:

### full

Log all events (default):

```yaml
logging:
  level: full
```

Events logged:
- request.received
- organization.lookup
- retrieval.completed
- policy.resolved
- enforcement.passed / enforcement.attached
- request.completed
- request.denied (on governance/policy denial)
- All stage-specific metrics and trace events

### minimal

Log only critical events:

```yaml
logging:
  level: minimal
```

Events logged:
- request.received
- org.resolved
- request.completed
- request.denied
- error.occurred

Use minimal logging to reduce storage and processing overhead while maintaining compliance audit trail.

## Accessing Audit Logs

### Using the AuditLogger

rag_control provides built-in audit logger implementations:

#### StructlogAuditLogger (Default)

Emits structured JSON logs using structlog:

```python
from rag_control.observability.audit_logger import StructlogAuditLogger
from rag_control import RAGControl

# Initialize audit logger
audit_logger = StructlogAuditLogger()

# Pass to RAGControl engine
engine = RAGControl(
    llm=llm,
    query_embedding=query_embedding,
    vector_store=vector_store,
    config=config,
    audit_logger=audit_logger
)

# Logs are automatically emitted during engine execution
result = engine.run(query, user_context)
```

#### NoOpAuditLogger

Disables audit logging (for testing):

```python
from rag_control.observability.audit_logger import NoOpAuditLogger

audit_logger = NoOpAuditLogger()

engine = RAGControl(
    # ... other params
    audit_logger=audit_logger
)
```

#### Custom Audit Logger

Implement a custom audit logger by following the `AuditLogger` protocol:

```python
from typing import Any, Literal
from rag_control.observability.audit_logger import AuditLogger, AuditLogLevel

class MyCustomAuditLogger:
    """Custom audit logger implementation"""

    def log_event(
        self,
        event: str,
        *,
        level: AuditLogLevel = "info",
        **fields: Any
    ) -> None:
        """Log an audit event to your custom system"""
        # Send to your logging system (database, API, message queue, etc.)
        print(f"[{level.upper()}] {event}: {fields}")

# Use it with RAGControl
custom_logger = MyCustomAuditLogger()

engine = RAGControl(
    llm=llm,
    query_embedding=query_embedding,
    vector_store=vector_store,
    config=config,
    audit_logger=custom_logger
)
```

**Protocol Requirements:**

Your custom logger must implement:
- `log_event(event: str, *, level: AuditLogLevel = "info", **fields: Any) -> None`
  - `event`: Event name (string)
  - `level`: Log level (debug, info, warning, error, critical)
  - `**fields`: Event-specific fields (org_id, request_id, etc.)

**Common Use Cases:**

```python
class DatabaseAuditLogger:
    """Store audit logs in a database"""

    def log_event(self, event: str, *, level: str = "info", **fields: Any) -> None:
        db.insert('audit_logs', {
            'event': event,
            'level': level,
            'timestamp': datetime.utcnow(),
            **fields
        })

class SlackAuditLogger:
    """Send critical events to Slack"""

    def log_event(self, event: str, *, level: str = "info", **fields: Any) -> None:
        if level in ['error', 'critical'] or event == 'request.denied':
            slack.send_message(
                channel='#audit-alerts',
                text=f"[{level}] {event}: {fields.get('error_message', '')}"
            )

class MultiAuditLogger:
    """Log to multiple destinations"""

    def __init__(self, loggers: list[AuditLogger]):
        self.loggers = loggers

    def log_event(self, event: str, *, level: str = "info", **fields: Any) -> None:
        for logger in self.loggers:
            try:
                logger.log_event(event, level=level, **fields)
            except Exception as e:
                # Swallow exceptions to ensure one logger failure doesn't affect others
                print(f"Logger failed: {e}")
```

### Log Output

Structlog outputs JSON-formatted logs to stdout:

```json
{
  "event": "request.received",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "org_id": "acme_corp",
  "user_id": "user-123",
  "mode": "run",
  "component": "rag_control.engine",
  "sdk_name": "rag_control",
  "sdk_version": "1.0.0",
  "company_name": "RetrievalLabs",
  "level": "info",
  "timestamp": "2026-03-04T10:30:00.000Z"
}
```

## Compliance & Retention

### Compliance Use Cases

Audit logs support:

- **Regulatory Compliance**: HIPAA, GDPR, SOC2
- **Incident Investigation**: Trace what happened and why
- **Access Audits**: Who accessed what, when, why
- **Policy Audits**: Were policies enforced correctly?

## Log Privacy

### Sensitive Data

By default, audit logs don't include:

- Actual query content (can be enabled)
- Response content
- Document content
- User credentials

## See Also

- [Distributed Tracing](/observability/distributed-tracing)
- [Metrics](/observability/metrics)
