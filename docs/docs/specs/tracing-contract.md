---
title: Tracing Contract
description: Formal specification of distributed tracing
---

# Tracing Contract

This document specifies the formal contract for rag_control distributed tracing.

## Overview

The Tracing Contract defines:

- Span hierarchy and naming
- Span attributes and semantics
- Context propagation
- Trace correlation
- OpenTelemetry compliance

## Detailed Specification

For the complete formal specification, see:

📄 [`rag_control/spec/tracing_contract.md`](https://github.com/RetrievalLabs/rag_control/blob/main/rag_control/spec/tracing_contract.md)

## Quick Reference

### Span Hierarchy

```
request_span (root)
├── org_lookup_span
├── document_filtering_span
├── embedding_span
├── retrieval_span
├── policy_resolution_span
├── prompt_building_span
├── llm_generation_span
├── enforcement_span
└── observability_span
```

### Root Span Attributes

- `request_id`: Unique request identifier
- `org_id`: Organization ID
- `user_id`: User ID
- `mode`: "run" or "stream"
- `status`: "ok" or "error"
- `duration_ms`: Total duration

### Stage Span Attributes

- `stage`: Stage name
- `duration_ms`: Stage duration
- Status-specific attributes

## See Also

- [Distributed Tracing](/observability/distributed-tracing)
- [Execution Contract](/specs/execution-contract)
- [GitHub Repository](https://github.com/RetrievalLabs/rag_control)
