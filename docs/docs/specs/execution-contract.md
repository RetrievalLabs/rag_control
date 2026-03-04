---
title: Execution Contract
description: Formal specification of rag_control execution behavior
---

# Execution Contract

This document specifies the formal contract for rag_control request execution and response guarantees.

## Overview

The Execution Contract defines:

- Request processing flow
- Policy enforcement behavior
- Response validation
- Error handling
- Observable state changes

## Detailed Specification

For the complete formal specification, see:

📄 [`rag_control/spec/execution_contract.md`](https://github.com/RetrievalLabs/rag_control/blob/main/rag_control/spec/execution_contract.md)

## Quick Reference

### Request Processing

1. Validate organization
2. Apply document filters
3. Embed query
4. Retrieve documents
5. Resolve policy
6. Generate response with policy constraints
7. Enforce policy constraints
8. Return response or denial

### Success Criteria

- Organization exists and user is authorized
- Documents retrieved (if required)
- Policy determined
- Enforcement checks passed
- Response contains proper metadata

### Failure Handling

- Organization validation fails → OrganizationError
- Retrieval fails → RetrievalError
- Policy not found → PolicyError
- Enforcement fails → PolicyEnforcementError
- LLM generation fails → LLMError

## See Also

- [Architecture Overview](/architecture/overview)
- [Execution Flow](/architecture/execution-flow)
- [GitHub Repository](https://github.com/RetrievalLabs/rag_control)
