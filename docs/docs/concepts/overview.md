---
title: Core Concepts Overview
description: Understanding the fundamental concepts of rag_control
---

# Core Concepts Overview

rag_control is built around several core concepts that work together to provide governance, security and observability for RAG systems.

## rag_control's Solution

rag_control provides a layered approach to governance:

```
User Request
    ↓
[Organization Validation]
    ↓
[Document Filtering]
    ↓
[Query Embedding]
    ↓
[Document Retrieval]
    ↓
[Policy Resolution]
    ↓
[LLM Generation]
    ↓
[Enforcement Checks]
    ↓
Response or Denial
```

## Core Concepts

### 1. Policies

**Policies** define how the LLM should behave:

- Generation parameters (temperature, output length)
- Citation requirements
- Knowledge restrictions
- Enforcement rules

Example: "Strict policy requires citations and prevents external knowledge"

### 2. Governance

**Governance** applies organization-level rules:

- Organization-specific policy overrides
- Role-based access control
- Data classification rules
- Conditional policy enforcement

Example: "Acme Corporation always uses strict policy for their queries"

### 3. Filters

**Filters** control document retrieval:

- Data classification (public, internal, confidential)
- Metadata-based filtering
- User context validation

Example: "Only retrieve documents marked for this organization"

### 4. Adapters

**Adapters** integrate rag_control with your infrastructure:

- LLM (language model)
- Embeddings (query encoding)
- Vector Store (document retrieval)

### 5. Observability

rag_control provides comprehensive observability:

- **Audit Logging**: Track every request and decision
- **Distributed Tracing**: Follow execution flow
- **Metrics**: Monitor performance and compliance

## Execution Flow

1. **Org Lookup**: Validate user's organization
2. **Document Filtering**: Apply org-level filters
3. **Query Embedding**: Encode the query
4. **Document Retrieval**: Fetch relevant documents
5. **Policy Resolution**: Determine applicable policy
6. **LLM Generation**: Generate response with policy constraints
7. **Enforcement**: Validate response against policy
8. **Audit**: Log request and decision

## Learning Path

1. **Start here**: You're reading it!
2. **Dig deeper**: [Policies](/concepts/policies)
3. **Understand governance**: [Governance](/concepts/governance)
4. **Learn filtering**: [Filters](/concepts/filters)
5. **Integrate adapters**: [Adapters](/concepts/adapters)

## See Also

- [Architecture Overview](/architecture/overview)
- [Quick Start](/getting-started/quick-start)
- [Configuration Guide](/getting-started/configuration)
