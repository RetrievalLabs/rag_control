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

## Filter Validation Rules

### Required Fields

Every filter must have:

- `name`: Unique identifier (lowercase, alphanumeric, underscores)
- `condition`: A valid condition object

### Condition Validation

| Validation | Rule | Example |
|-----------|------|---------|
| Required `field` | Must specify which field to check | ✓ `field: metadata.classification` |
| Required `operator` | Must be a valid operator | ✓ `operator: equals` ❌ `operator: match` |
| Required `value` | Value depends on operator | ✓ `value: public` ❌ Missing |
| Required `source` | Must be `user` or `documents` | ✓ `source: documents` |
| `document_match` only for documents | Only when `source: documents` | ✓ Required for documents, forbidden for user |

### Validation Errors

```python
# Invalid operator
ValueError("operator 'match' not supported, use one of: equals, contains, in, etc.")

# Missing document_match
ValueError("filter 'public_docs': source=documents requires document_match (any or all)")

# Invalid source
ValueError("filter 'user_check': source must be 'user' or 'documents', got 'context'")

# Duplicate filter names
ValueError("filter name 'public_only' is duplicated")

# Inconsistent value types
ValueError("filter 'numeric_check': operator 'lte' requires numeric value, got string")
```

## Performance Considerations

### Filter Efficiency

1. **Push-Down Filters**: Most efficient - applied at vector store level
   - Reduces network transfer
   - Reduces post-retrieval processing
   - Supported by: Pinecone, Weaviate, Milvus, PostgreSQL pgvector

2. **Post-Retrieval Filtering**: Less efficient but works with all stores
   - Applied after vector search returns results
   - Increases latency
   - May need to fetch more candidates to get top_k results

3. **Optimization Strategy**:
   - Start with post-retrieval filtering (simple, works everywhere)
   - Migrate to push-down filters as vector store supports it
   - Monitor filter selectivity (% of results excluded)

### Selectivity Impact

```yaml
# Example performance impact
filters:
  - enterprise_only        # 70% of docs excluded → fetch 3x candidates
  - internal_only          # 50% of docs excluded
  - active_documents       # 10% of docs excluded

# Total selectivity: 0.3 × 0.5 × 0.9 = 13.5% of docs remain
# To get top_k=10 documents, may need to fetch 100+ candidates
```

**Recommendation**: Monitor filter selectivity and adjust `top_k` accordingly.

## Best Practices

### 1. Design Hierarchical Filters

```yaml
# Instead of combining classifications:
- name: tier1_and_public
  condition:
    field: metadata.tier_and_classification
    operator: equals
    value: "tier1-public"
    source: documents
    document_match: all

# Better: Separate concerns
- name: tier1_only
  condition:
    field: metadata.tier
    operator: equals
    value: 1
    source: documents
    document_match: all

- name: public_only
  condition:
    field: metadata.classification
    operator: equals
    value: public
    source: documents
    document_match: all
```

### 2. Use Consistent Metadata Schema

**Good:**
```yaml
metadata:
  classification: string     # Always populated
  source: string            # Consistent enum: internal, external, web
  sensitivity_score: number # 1-10 scale
  created_date: ISO8601     # Standard format
```

**Avoid:**
```yaml
metadata:
  classification: string or null  # Inconsistent
  source: string or list         # Sometimes array
  sensitivity: number or string  # Variable type
  dates: mixed formats           # "2026-03-01" or "March 1 2026"
```

### 3. Document Filters Clearly

```yaml
- name: research_team_access
  description: |
    Researchers can access internal and confidential documents
    but NOT secret-level documents.
    Used for internal research and analysis.
    See governance policy section 3.2 for more details.
  condition:
    field: metadata.classification
    operator: in
    value: [internal, confidential]
    source: documents
    document_match: all
```

### 4. Start Permissive, Tighten Over Time

```yaml
# Phase 1: Minimal filtering
filters: []  # No filters, collect metadata

# Phase 2: Basic classification
filters:
  - public_only

# Phase 3: Add organization boundaries
filters:
  - public_only
  - organization_specific

# Phase 4: Add sensitivity controls
filters:
  - public_only
  - organization_specific
  - sensitivity_appropriate_for_role
  - active_documents
```

### 5. Test Filter Selectivity

Verify filters work effectively with your data:

```python
# Test before deploying
def test_filter_selectivity():
    # Without filters: 100 documents retrieved
    # With filters: 30 documents retrieved
    # Selectivity: 70% excluded

    # This is good - filters are working
    # If selectivity is 0-5%, filters may be too permissive
    # If selectivity is 95%+, filters may be too restrictive
    pass
```

### 6. Use Filter Descriptions

```yaml
- name: enterprise_customers
  description: |
    ✓ Include: Enterprise tier organizations
    ✗ Exclude: Free, Standard, Trial tiers

    This filter ensures only paying enterprise
    customers can access premium content.
  condition:
    field: org_tier
    operator: equals
    value: enterprise
    source: user
```

### 7. Combine with Governance Rules

Use filters alongside governance rules for complete control:

```yaml
# governance.md defines WHO can make requests
policy_rules:
  - name: deny_free_tier_in_production
    priority: 100
    effect: deny
    when:
      - field: org_tier
        operator: equals
        value: free
        source: user

# filters.md defines WHAT they can access
filters:
  - name: public_only
    condition:
      field: metadata.classification
      operator: equals
      value: public
      source: documents
      document_match: all
```

## Complex Filtering Scenarios

### Multi-Tier Customer Access

```yaml
filters:
  - name: free_tier_public
    description: Free tier can only see public documents
    condition:
      field: metadata.classification
      operator: equals
      value: public
      source: documents
      document_match: all

  - name: standard_tier_internal
    description: Standard tier can see public and internal
    condition:
      field: metadata.classification
      operator: in
      value: [public, internal]
      source: documents
      document_match: all

  - name: enterprise_tier_all
    description: Enterprise tier can see everything
    condition:
      field: metadata.classification
      operator: in
      value: [public, internal, confidential]
      source: documents
      document_match: all

orgs:
  - org_id: customer_free
    document_policy:
      filters: [free_tier_public]

  - org_id: customer_standard
    document_policy:
      filters: [standard_tier_internal]

  - org_id: customer_enterprise
    document_policy:
      filters: [enterprise_tier_all]
```

### Department-Based Access

```yaml
filters:
  - name: finance_only
    condition:
      field: metadata.departments
      operator: contains
      value: finance
      source: documents
      document_match: all

  - name: hr_only
    condition:
      field: metadata.departments
      operator: contains
      value: hr
      source: documents
      document_match: all

  - name: general_company
    condition:
      field: metadata.is_public_company_document
      operator: equals
      value: true
      source: documents
      document_match: all

orgs:
  - org_id: finance_team
    document_policy:
      filters: [finance_only, general_company]

  - org_id: hr_team
    document_policy:
      filters: [hr_only, general_company]
```

### Compliance-Based Filtering

```yaml
filters:
  - name: gdpr_compliant
    description: GDPR compliant documents only
    condition:
      field: metadata.gdpr_compliant
      operator: equals
      value: true
      source: documents
      document_match: all

  - name: hipaa_compliant
    description: HIPAA compliant documents only
    condition:
      field: metadata.hipaa_compliant
      operator: equals
      value: true
      source: documents
      document_match: all

  - name: sox_compliant
    description: SOX compliant documents only
    condition:
      field: metadata.sox_compliant
      operator: equals
      value: true
      source: documents
      document_match: all

orgs:
  - org_id: eu_operations
    document_policy:
      filters: [gdpr_compliant]

  - org_id: healthcare_division
    document_policy:
      filters: [hipaa_compliant]

  - org_id: financial_division
    document_policy:
      filters: [sox_compliant]
```

## Troubleshooting

### Issue: Filters Not Applied

**Check:**
1. Filters are referenced in organization's `document_policy.filters`
2. Vector store adapter implements filter support
3. Document metadata contains the fields being filtered

### Issue: Too Many Documents Filtered Out

**Solutions:**
1. Review filter selectivity - may be too restrictive
2. Check metadata consistency - missing or wrong values
3. Loosen filter conditions (use `in` instead of `equals`)
4. Increase `top_k` to compensate

### Issue: Filter Performance Degradation

**Solutions:**
1. Implement push-down filters if vector store supports it
2. Monitor filter selectivity
3. Use more efficient operators (`equals` faster than `contains`)
4. Index metadata fields in vector store

## See Also

- [Vector Store Adapter](./vector-store-adapter) - Implementation guide
- [Governance](/concepts/governance) - Organization-level rules
- [Policies](/concepts/policies) - LLM generation policies
- [Configuration Guide](/getting-started/configuration) - Complete config reference
