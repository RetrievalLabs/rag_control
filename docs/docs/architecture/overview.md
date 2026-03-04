---
title: Architecture Overview
description: Understanding the rag_control architecture
---

# Architecture Overview

rag_control is architected as a layered governance and execution engine for RAG systems.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Request                         │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 Execution Engine                        │
├──────────────────────────────────────────────────────────┤
│  ├─ Organization Validation                             │
│  ├─ Document Filtering                                  │
│  ├─ Query Embedding                                     │
│  ├─ Document Retrieval                                  │
│  ├─ Policy Resolution                                   │
│  ├─ LLM Generation (with policy constraints)            │
│  ├─ Enforcement Checks                                  │
│  └─ Observability (audit, tracing, metrics)             │
└────────────────┬───────────────────────────────┬────────┘
                 ↓                               ↓
    ┌──────────────────────┐      ┌──────────────────────┐
    │  Response / Denial   │      │  Observability Data  │
    └──────────────────────┘      └──────────────────────┘
```

## Core Components

### Execution Engine

The central orchestrator that:
- Validates organization context
- Applies governance rules
- Coordinates adapter calls
- Enforces policies
- Records observability events

### Policy Registry

Manages generation and enforcement policies:
- Policy definitions
- Generation parameters (temperature, output length)
- Citation requirements
- Enforcement rules

### Governance Registry

Applies organization-level rules:
- Organization-specific configurations
- Policy resolution rules (conditional)
- Access controls
- Data classification mappings

### Filter Registry

Manages document retrieval filters:
- Data classification filters
- Metadata-based filters
- Organization-specific filters

### Adapters

Pluggable implementations for:
- **LLM Adapter**: Language model access
- **Query Embedding Adapter**: Query vectorization
- **Vector Store Adapter**: Document retrieval

### Observability

Three-pillar approach:
- **Audit Logging**: Full request/response tracking
- **Distributed Tracing**: Execution flow visualization
- **Metrics**: Performance and compliance monitoring

## Execution Flow

Detailed step-by-step execution:

```
1. Validate Organization
   └─ Verify user's org_id exists
   └─ Load org configuration

2. Apply Document Filters
   └─ Execute org-specific filters
   └─ Determine retrieval parameters

3. Embed Query
   └─ Convert query to vector via embedding adapter
   └─ Track embedding dimensions

4. Retrieve Documents
   └─ Search vector store with top_k
   └─ Return document scores and content

5. Resolve Policy
   └─ Evaluate governance rules
   └─ Apply conditional enforcement
   └─ Determine applicable policy

6. Build Prompt
   └─ Format documents in context
   └─ Prepare policy-aware prompt

7. Generate Response
   └─ Call LLM with policy parameters
   └─ Temperature, max_tokens from policy
   └─ Return generated content

8. Enforce Constraints
   └─ Validate citations if required
   └─ Check external knowledge restrictions
   └─ Block or allow response

9. Record Observability
   └─ Emit audit events
   └─ Record traces and metrics
   └─ Track policy decisions

10. Return Result
    └─ Response if enforcement passed
    └─ Denial error if enforcement failed
```

## Design Principles

### 1. Security Through Governance

Policies and governance rules prevent misuse at request time, not just response time.

### 2. Exception-Safe Pattern

Governance failures don't break request flow:
- Graceful fallbacks
- Exceptions caught and converted to denials
- Never propagate governance errors

### 3. Observable by Default

Every decision is tracked:
- Audit logs for compliance
- Traces for debugging
- Metrics for monitoring

### 4. Pluggable Adapters

No hard dependencies on specific LLM or vector store:
- Implement adapter interfaces
- Swap implementations without code changes
- Support multiple concurrent adapters

### 5. Zero-Trust on Retrieval

All retrieved documents are treated as untrusted:
- Citations validated
- External knowledge checked
- Knowledge restrictions enforced

## Layers

### Request Layer
- User context validation
- Organization verification
- Initial parameter validation

### Retrieval Layer
- Document filtering
- Query embedding
- Vector search

### Governance Layer
- Policy resolution
- Conditional rule evaluation
- Access control

### Generation Layer
- Prompt engineering
- LLM invocation
- Policy-constrained generation

### Enforcement Layer
- Citation validation
- Knowledge restriction checks
- Response validation

### Observability Layer
- Audit event recording
- Distributed trace creation
- Metrics collection

## Failure Modes

rag_control handles failures gracefully:

### Adapter Failures
- LLM unavailable → Return error response
- Embedding service down → Return error response
- Vector store timeout → Return error response

### Governance Failures
- Invalid organization → Deny request
- Missing policy → Use default policy
- Rule evaluation error → Log and continue

### Enforcement Failures
- Citations invalid → Block response (if configured)
- External knowledge detected → Block response (if configured)

All failures are logged and metricated.

## Performance Characteristics

### Latency

Typical latency breakdown:

| Stage | Time |
|-------|------|
| Organization validation | `<1ms` |
| Document filtering | `<5ms` |
| Query embedding | 100-500ms (LLM dependent) |
| Document retrieval | 10-100ms (index dependent) |
| Policy resolution | `<1ms` |
| LLM generation | 1-5s (model dependent) |
| Enforcement checks | `<50ms` |
| Observability | `<10ms` |
| **Total** | **1-5s** (mostly LLM) |

### Throughput

Limited by LLM throughput, not rag_control.

## Scalability

- Stateless design (no local caching)
- Horizontal scaling via multiple engine instances
- Adapter scalability depends on external services

## See Also

- [Execution Flow](/architecture/execution-flow)
- [Components](/architecture/components)
- [Core Concepts](/concepts/overview)
