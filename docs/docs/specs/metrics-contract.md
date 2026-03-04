---
title: Metrics Contract
description: Formal specification of metrics and observability
---

# Metrics Contract

This document specifies the formal contract for rag_control metrics and observability.

## Overview

The Metrics Contract defines:

- 18+ metrics covering throughput, latency, quality, costs, and errors
- Metric types (counters, histograms, gauges)
- Standard labels and dimensions
- Collection guarantees
- Cardinality and retention

## Detailed Specification

For the complete formal specification, see:

📄 [`rag_control/spec/metrics_contract.md`](https://github.com/RetrievalLabs/rag_control/blob/main/rag_control/spec/metrics_contract.md)

## Quick Reference

### Metric Categories

- **Request & Latency**: requests (counter), request.duration_ms (histogram)
- **Stage Tracking**: stage.duration_ms (histogram for each stage)
- **Retrieval**: document_count, document_score, top_document_score (histograms)
- **Query**: query.length_chars (histogram)
- **Policy**: policy.resolved_by_name (counter)
- **LLM**: prompt_tokens, completion_tokens, total_tokens (counters), token_efficiency (histogram)
- **Embedding**: embedding.dimensions (histogram)
- **Error Tracking**: errors_by_type, errors_by_category (counters)
- **Denials**: requests.denied (counter, governance/enforcement/policy only)

### Standard Labels

- `mode`: "run" or "stream"
- `org_id`: organization identifier
- `status`: "ok" or "error"

## See Also

- [Metrics & Observability](/observability/metrics)
- [Execution Contract](/specs/execution-contract)
- [GitHub Repository](https://github.com/RetrievalLabs/rag_control)
