---
title: Execution Flow
description: Detailed execution flow in rag_control
---

# Execution Flow

This document details the step-by-step execution flow when processing a request through rag_control.

## Request to Response Pipeline

```
User Request
    ↓
[Stage 1: Organization Lookup]
    ↓
[Stage 2: Document Filtering]
    ↓
[Stage 3: Query Embedding]
    ↓
[Stage 4: Document Retrieval]
    ↓
[Stage 5: Policy Resolution]
    ↓
[Stage 6: Prompt Building]
    ↓
[Stage 7: LLM Generation]
    ↓
[Stage 8: Enforcement Checks]
    ↓
[Stage 9: Observability Recording]
    ↓
Response or Denial
```

## Stage Details

### Stage 1: Organization Lookup

**Purpose**: Validate organization context

**Operations**:
1. Extract `org_id` from user context
2. Look up organization in governance registry
3. Load organization configuration
4. Validate user has access

**Outputs**:
- Organization object
- Default policy
- Document policy settings
- Policy rules

**Errors**:
- `OrganizationNotFoundError`: org_id doesn't exist
- `UnauthorizedError`: User not authorized for org

### Stage 2: Document Filtering

**Purpose**: Apply organization-level retrieval filters

**Operations**:
1. Get org-specific filters
2. For each filter:
   - Evaluate filter condition
   - Mark as "will apply"
3. Prepare retrieval constraints

**Outputs**:
- Resolved filters to apply
- Retrieval metadata

**Notes**:
- Filters are evaluated before retrieval
- Multiple filters are ANDed together
- Prepared but not yet applied

### Stage 3: Query Embedding

**Purpose**: Convert query to vector for search

**Operations**:
1. Call query embedding adapter
2. Validate embedding dimensions
3. Record embedding metrics

**Outputs**:
- Query embedding vector
- Embedding dimensions

**Errors**:
- `EmbeddingError`: Adapter failure
- `ValidationError`: Dimension mismatch

### Stage 4: Document Retrieval

**Purpose**: Search for relevant documents

**Operations**:
1. Call vector store adapter
2. Pass:
   - Query embedding
   - top_k from org configuration
   - org_id for filtering
3. Receive retrieved documents
4. Apply filters to results
5. Record document scores

**Outputs**:
- Retrieved documents with scores
- Document count

**Errors**:
- `RetrievalError`: Vector store failure
- `FilterError`: Filter application failed

### Stage 5: Policy Resolution

**Purpose**: Determine which policy to apply

**Operations**:
1. Load organization policy rules
2. Sort by priority (descending)
3. For each rule:
   - Evaluate `when` conditions
   - Check user context and documents
   - On match:
     - If effect is "deny": raise denial
     - If effect is "enforce": use policy
4. If no rule matches: use default policy

**Outputs**:
- Selected policy
- Policy name
- Resolved by (rule name or default)

**Errors**:
- `PolicyNotFoundError`: Policy doesn't exist
- `InvalidRuleError`: Rule condition invalid

### Stage 6: Prompt Building

**Purpose**: Create LLM prompt with context

**Operations**:
1. Format retrieved documents
2. Add policy instructions
3. Add policy constraints
4. Format user query
5. Build complete prompt

**Outputs**:
- Formatted prompt
- Prompt statistics (length, tokens)

### Stage 7: LLM Generation

**Purpose**: Generate response using LLM

**Operations**:
1. Call LLM adapter with:
   - Prompt from stage 6
   - temperature from policy
   - max_tokens from policy
2. Receive response
3. Extract response content
4. Count tokens

**Outputs**:
- Generated response text
- Token counts (prompt + completion)

**Errors**:
- `LLMError`: LLM adapter failure
- `TimeoutError`: LLM call timeout
- `RateLimitError`: Rate limit exceeded

### Stage 8: Enforcement Checks

**Purpose**: Validate response against policy

**Operations**:

If `enforce.validate_citations`:
1. Parse citations from response
2. Match citations to retrieved documents
3. Verify all claims are cited (if required)
4. If invalid and `block_on_missing_citations`: deny

If `enforce.prevent_external_knowledge`:
1. Check response for claims
2. Verify claims match document content
3. If external knowledge found: deny

If all checks pass:
1. Mark enforcement as passed
2. Proceed to observability

**Outputs**:
- Enforcement status (passed/denied)
- Validation details

**Errors**:
- `EnforcementError`: Policy validation failed

### Stage 9: Observability Recording

**Purpose**: Record request lifecycle for compliance and monitoring

**Operations**:

Audit Logging:
1. Record request event
2. Record policy decision
3. Record enforcement result
4. Record token usage

Distributed Tracing:
1. Create root request span
2. Create spans for each stage
3. Record stage durations
4. Link related operations

Metrics:
1. Request counter
2. Stage latencies
3. Token usage
4. Error metrics
5. Policy decision metrics

**Outputs**:
- Audit events
- Trace data
- Metric increments

## Error Handling

### Error Categories

**Governance Errors**:
- Organization not found
- Unauthorized access
- Policy not found
- Invalid rule

**Retrieval Errors**:
- Embedding service failure
- Vector store failure
- Document filtering failure

**Generation Errors**:
- LLM service failure
- Rate limiting
- Timeout

**Enforcement Errors**:
- Citation validation failure
- Knowledge restriction violation

### Exception Handling Pattern

```python
try:
    # Execute stage
    result = execute_stage()
except Exception as e:
    # Log error
    logger.error(f"Stage failed: {e}")

    # Record metrics
    metrics.record_error(error_type=type(e).__name__)

    # Return error response
    return ErrorResponse(error=e)
```

## Performance Optimization

### Caching

- Organization configs: cached at engine initialization
- Filter conditions: evaluated once
- Policy rules: loaded once

### Parallel Operations

- Document retrieval and policy resolution can run in parallel
- Not currently implemented but possible

### Lazy Evaluation

- Policy rules evaluated in priority order, stop on first match
- Filters evaluated only if needed

## Request Tracing Example

For a typical request:

```
request_span (total: 2.5s)
├── org_lookup_span (5ms)
│   └── Load org config
├── document_filtering_span (10ms)
│   └── Apply 3 filters
├── embedding_span (350ms)
│   └── Call embedding service
├── retrieval_span (75ms)
│   └── Vector search + filtering
├── policy_resolution_span (2ms)
│   └── Evaluate 2 rules
├── llm_generation_span (2000ms)
│   └── Call GPT-4
├── enforcement_span (40ms)
│   └── Validate citations
└── observability_span (18ms)
    └── Record metrics and logs
```

## Streaming Requests

Streaming follows the same flow through stage 7 (LLM Generation):

1. Stages 1-6: Same as above
2. Stage 7: Stream LLM response
   - Call `stream()` instead of `generate()`
   - Yield tokens as they arrive
3. Stage 8: Enforcement
   - Can validate accumulated response
   - Or defer to batch validation
4. Stage 9: Observability
   - Record once streaming complete

## See Also

- [Architecture Overview](/architecture/overview)
- [Components](/architecture/components)
- [Tracing Contract](/specs/tracing-contract)
