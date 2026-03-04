---
title: Audit Log Contract
description: Formal specification of audit logging behavior
---

# Audit Log Contract

This document specifies the formal contract for rag_control audit logging.

## Overview

The Audit Log Contract defines:

- Audit event types
- Event structure and fields
- Logging guarantees
- Log ordering and consistency
- Retention requirements

## Detailed Specification

For the complete formal specification, see:

📄 [`rag_control/spec/audit_log_contract.md`](https://github.com/RetrievalLabs/rag_control/blob/main/rag_control/spec/audit_log_contract.md)

## Quick Reference

### Guaranteed Events

- Request received
- Organization lookup result
- Policy resolved
- Enforcement result
- Request completed or denied
- Any errors that occur

### Event Structure

All events include:
- `event`: Event type
- `request_id`: Unique request identifier
- `timestamp`: ISO 8601 timestamp
- `org_id`: Organization ID
- `user_id`: User ID

### Compliance

- Logs are tamper-evident
- All requests are logged (when enabled)
- No sensitive data by default (unless configured)
- Retention configurable per policy

## See Also

- [Audit Logging](/observability/audit-logging)
- [Metrics Contract](/specs/metrics-contract)
- [GitHub Repository](https://github.com/RetrievalLabs/rag_control)
