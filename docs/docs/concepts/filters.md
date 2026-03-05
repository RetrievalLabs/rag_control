---
title: Filters
description: Comprehensive guide to document filtering, metadata filtering, and vector store integration
---

# Filters

Filters control what documents can be retrieved, providing data classification, access control, and content filtering at the retrieval level. Filters ensure users only see documents they're authorized to access.

## What is a Filter?

A filter is a rule that determines whether a document should be included in retrieval results based on:

- **Document metadata** (classification, source, owner, sensitivity)
- **User context** (organization, role, clearance level, tier)
- **Content attributes** (confidentiality, sensitivity score, freshness)

Filters operate **after vector search** to narrow down results to only those the user is authorized to access. This protects sensitive data while maintaining semantic relevance.

## Core Concepts

### Filter vs. Governance vs. Policy

These systems work together but at different levels:

| System | Level | Purpose | Example |
|--------|-------|---------|---------|
| **Filter** | Retrieval | What documents can be retrieved | "Only internal documents" |
| **Governance** | Organization | Who can access what | "Enterprise users get strict policy" |
| **Policy** | Generation | How LLM generates responses | "Require citations" |

**Example flow:**
```
Request arrives
  ↓
Governance evaluates: Is this user allowed? → Selects policy
  ↓
Filters applied: Which documents can this user see? → Narrows results
  ↓
Policy enforced: How should LLM generate? → Constrains generation
  ↓
Response returned
```

## Filter Structure

A complete filter includes:

```yaml
filters:
  - name: enterprise_only
    description: Only retrieve documents accessible to enterprise customers
    condition:
      field: metadata.required_tier
      operator: equals
      value: enterprise
      source: documents
      document_match: all
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique filter identifier (lowercase, underscores) |
| `condition` | object | The condition that must match |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable explanation of the filter |

## Condition Structure

Every filter has exactly one condition with these fields:

```yaml
condition:
  field: metadata.classification      # What field to check
  operator: equals                    # How to compare
  value: public                       # What to compare against
  source: documents                   # Where to get the field (user or documents)
  document_match: all                 # For documents: any or all
```

### Condition Fields

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `field` | string | Both | Field name (supports nested paths like `metadata.owner.department`) |
| `operator` | string | Both | Comparison operator (equals, contains, in, lt, gt, etc.) |
| `value` | any | Both | Expected value to compare against |
| `source` | string | Both | `user` for user context, `documents` for document metadata |
| `document_match` | string | Documents only | `any` (at least one doc matches) or `all` (every doc must match) |

## Operators Reference

### Equality Operators

| Operator | Type | Description | Example |
|----------|------|-------------|---------|
| `equals` | All | Exact match | `classification equals "public"` |
| `not_equals` | All | Not equal to value | `status not_equals "archived"` |

### Collection Operators

| Operator | Type | Description | Example |
|----------|------|-------------|---------|
| `in` | All | Value in list | `source in [internal, proprietary]` |
| `not_in` | All | Value not in list | `tier not_in [free, trial]` |
| `contains` | String | String contains substring | `tags contains "confidential"` |
| `not_contains` | String | String does not contain | `tags not_contains "deprecated"` |

### Numeric Operators

| Operator | Type | Description | Example |
|----------|------|-------------|---------|
| `gt` | Numeric | Greater than | `sensitivity gt 7` |
| `gte` | Numeric | Greater than or equal | `age_days gte 0` |
| `lt` | Numeric | Less than | `confidentiality_score lt 50` |
| `lte` | Numeric | Less than or equal | `required_clearance_level lte user_clearance` |

## Sources: User vs. Documents

### Source: user

Check fields from the user's context:

```yaml
condition:
  field: org_tier
  operator: equals
  value: enterprise
  source: user
  # document_match not needed - single value from user
```

Available user fields: `org_id`, `user_id`, `org_tier`, `role`, and custom attributes.

**Use case:** Filter based on who is making the request

**Example:**
```yaml
- name: premium_only
  description: Only available to premium tier users
  condition:
    field: org_tier
    operator: equals
    value: premium
    source: user
```

### Source: documents

Check metadata from each document:

```yaml
condition:
  field: metadata.classification
  operator: equals
  value: public
  source: documents
  document_match: all      # REQUIRED for documents source
```

**Use case:** Filter based on document properties

**Example:**
```yaml
- name: public_documents
  description: Only retrieve publicly available documents
  condition:
    field: metadata.classification
    operator: equals
    value: public
    source: documents
    document_match: all
```

## Document Matching: any vs. all

When `source: documents`, you must specify how to match:

### document_match: any

Include document if **at least one** document in the retrieval result set matches:

```yaml
condition:
  field: metadata.source
  operator: equals
  value: verified
  source: documents
  document_match: any   # Pass if ANY doc is verified
```

**Behavior:** More permissive, includes documents if condition matches any retrieved document

### document_match: all

Include document if **ALL** documents in the retrieval result set match:

```yaml
condition:
  field: metadata.classification
  operator: equals
  value: internal
  source: documents
  document_match: all   # Pass only if ALL docs are internal
```

**Behavior:** More restrictive, requires all documents to match

## Vector Store Adapter Support

Filters are applied during document retrieval and **must be supported by the vector_store_adapter**. The adapter is responsible for:

1. **Accepting Filters**: Receive filter definitions from the configuration
2. **Applying Filters at Retrieval**: Use filters when querying the vector store
3. **Metadata-Based Filtering**: Filter documents based on their metadata and user context

The adapter must support:
- Filtering by document metadata fields (any field in document metadata)
- Filtering by user context (org_id, role, tier, custom attributes)
- Multiple filters with AND logic (all filters must pass)
- All supported operators: `equals`, `contains`, `in`, `gt`, `lt`, `gte`, `lte`, etc.
- Nested field paths (e.g., `metadata.owner.department`)
- Document matching modes: `any` and `all`

When implementing a vector store adapter, ensure it applies configured filters to filter results based on user authorization and data accessibility rules.

## Filter Examples

### Data Classification Filters

**Retrieve only public documents:**

```yaml
- name: public_only
  description: Retrieve only publicly available documents
  condition:
    field: metadata.classification
    operator: equals
    value: public
    source: documents
    document_match: all
```

**Exclude confidential documents:**

```yaml
- name: exclude_confidential
  description: Do not retrieve confidential documents
  condition:
    field: metadata.classification
    operator: not_equals
    value: confidential
    source: documents
    document_match: all
```

**Allow internal or higher classification:**

```yaml
- name: internal_and_above
  description: Allow internal and higher classification levels
  condition:
    field: metadata.classification
    operator: in
    value: [internal, confidential, secret]
    source: documents
    document_match: all
```

### Organization Filters

**Enterprise customers only:**

```yaml
- name: enterprise_customers
  description: Only for enterprise tier customers
  condition:
    field: org_tier
    operator: equals
    value: enterprise
    source: user
```

**Specific organization documents:**

```yaml
- name: acme_only
  description: Only documents belonging to Acme Corporation
  condition:
    field: metadata.owner_org_id
    operator: equals
    value: acme_corp
    source: documents
    document_match: all
```

**Multi-organization access:**

```yaml
- name: partner_organizations
  description: Allow documents from partner organizations
  condition:
    field: metadata.owner_org_id
    operator: in
    value: [acme_corp, techstart_inc, global_enterprises]
    source: documents
    document_match: all
```

### Source/Origin Filters

**Internal sources only:**

```yaml
- name: internal_only
  description: Only internally sourced documents
  condition:
    field: metadata.source
    operator: in
    value: [internal_wiki, internal_docs, intranet]
    source: documents
    document_match: all
```

**Exclude web content:**

```yaml
- name: no_web_content
  description: Exclude publicly scraped web documents
  condition:
    field: metadata.source
    operator: not_equals
    value: public-web
    source: documents
    document_match: all
```

**Verified sources only:**

```yaml
- name: verified_sources
  description: Only documents from verified, trusted sources
  condition:
    field: metadata.is_verified
    operator: equals
    value: true
    source: documents
    document_match: all
```

### Sensitivity/Access Filters

**Premium user access:**

```yaml
- name: premium_access
  description: Premium users can access more sensitive documents
  condition:
    field: metadata.sensitivity_score
    operator: lte
    value: 8
    source: documents
    document_match: all
```

**Role-based sensitivity:**

```yaml
- name: analyst_access
  description: Analysts can view up to sensitivity level 7
  condition:
    field: metadata.sensitivity_score
    operator: lte
    value: 7
    source: documents
    document_match: all
```

### Time-based Filters

**Recent documents only:**

```yaml
- name: recent_documents
  description: Only documents updated in last 30 days
  condition:
    field: metadata.updated_at_days_ago
    operator: lte
    value: 30
    source: documents
    document_match: all
```

**Exclude archived documents:**

```yaml
- name: active_documents
  description: Exclude archived documents
  condition:
    field: metadata.is_archived
    operator: equals
    value: false
    source: documents
    document_match: all
```

### Complex Tag-based Filters

**Exclude deprecated content:**

```yaml
- name: no_deprecated
  description: Exclude documents tagged as deprecated
  condition:
    field: metadata.tags
    operator: not_contains
    value: deprecated
    source: documents
    document_match: all
```

**Require specific tags:**

```yaml
- name: requires_approval_tag
  description: Only approved documents
  condition:
    field: metadata.tags
    operator: contains
    value: approved
    source: documents
    document_match: all
```

## Applying Filters in Organizations

Filters are referenced in organization configurations:

```yaml
orgs:
  - org_id: acme_corp
    description: Acme Corporation
    default_policy: strict_citations
    document_policy:
      top_k: 8
      filters:
        - enterprise_only
        - internal_only
```

### Multiple Filters (AND Logic)

When multiple filters are specified, **ALL filters must pass**:

```yaml
document_policy:
  filters:
    - enterprise_only        # AND
    - internal_only          # AND
    - exclude_confidential   # AND
    - active_documents       # All four must be true
```

This is equivalent to: `(enterprise_only) AND (internal_only) AND (exclude_confidential) AND (active_documents)`

### No OR Logic

Filters always use AND logic. If you need OR logic, you must:

1. Create multiple organizations with different filter sets, or
2. Use a single compound filter with `in` operator

**Example - OR logic via in operator:**

Instead of:
```yaml
filters: [source_is_internal, source_is_proprietary]  # Not how OR works
```

Use:
```yaml
filters:
  - name: internal_or_proprietary
    condition:
      field: metadata.source
      operator: in
      value: [internal, proprietary]
      source: documents
      document_match: all
```

## Filter Resolution Flow

When retrieving documents:

```
User request arrives
  ↓
Extract user_context and filters from org config
  ↓
Call vector_store_adapter.retrieve_with_filters()
  ↓
Adapter performs vector search
  ↓
Adapter applies filters to results:
  For each document:
    ├─ Check filter 1 condition (must pass)
    ├─ Check filter 2 condition (must pass)
    ├─ Check filter N condition (must pass)
    ├─ All pass? → Include document
    └─ Any fail? → Exclude document
  ↓
Return filtered documents (up to top_k)
  ↓
Policy applied to response
  ↓
Return to user
```

## See Also

- [Vector Store Adapter](./vector-store-adapter) - Implementation guide
- [Governance](/concepts/governance) - Organization-level rules
- [Policies](/concepts/policies) - LLM generation policies
- [Configuration Guide](/getting-started/configuration) - Complete config reference
