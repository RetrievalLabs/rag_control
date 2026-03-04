---
title: Filters
description: Understanding rag_control document filters
---

# Filters

Filters control what documents can be retrieved, providing data classification and access control at the retrieval level.

## What is a Filter?

A filter is a rule that determines whether a document should be included in retrieval based on:

- Document metadata (classification, source, owner)
- User context (organization, role, clearance)
- Content attributes (sensitivity, confidentiality)

Filters operate on the retrieved documents to ensure users only see what they're authorized to see.

## Filter Structure

```yaml
filters:
  - name: enterprise_only
    description: Only retrieve enterprise documents
    condition:
      field: org_tier
      operator: equals
      value: enterprise
      source: user
```

## Filter Conditions

A filter has a single condition that must be satisfied:

### Condition Fields

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field to check (document or user context) |
| `operator` | string | Comparison operator |
| `value` | any | Value to compare against |
| `source` | string | `user` or `documents` |
| `document_match` | string | `any` or `all` (documents only) |

### Operators

- `equals`: Exact match
- `contains`: String contains substring
- `in`: Value in list
- `not_equals`: Not equal
- `not_contains`: Does not contain
- `gt`: Greater than (numeric)
- `lt`: Less than (numeric)
- `gte`: Greater than or equal
- `lte`: Less than or equal

### Sources

**user**: Check user context fields

```yaml
condition:
  field: org_tier
  operator: equals
  value: enterprise
  source: user
```

**documents**: Check document metadata

```yaml
condition:
  field: metadata.classification
  operator: equals
  value: public
  source: documents
  document_match: any  # any or all
```

## Document Matching

When filtering documents:

- **any**: Include document if ANY document in result set matches
- **all**: Include document if ALL documents in result set match

## Filter Examples

### Data Classification Filters

Retrieve only public documents:

```yaml
- name: public_only
  description: Retrieve only public documents
  condition:
    field: metadata.classification
    operator: equals
    value: public
    source: documents
    document_match: all
```

Exclude confidential documents:

```yaml
- name: exclude_confidential
  description: Exclude confidential documents
  condition:
    field: metadata.classification
    operator: not_equals
    value: confidential
    source: documents
    document_match: all
```

### Organization Filters

Enterprise customers only:

```yaml
- name: enterprise_customers
  description: Only for enterprise tier customers
  condition:
    field: org_tier
    operator: equals
    value: enterprise
    source: user
```

Specific organization:

```yaml
- name: acme_only
  description: Only Acme Corporation documents
  condition:
    field: metadata.owner_org_id
    operator: equals
    value: acme_corp
    source: documents
    document_match: all
```

### Source Filters

Only internal documents:

```yaml
- name: internal_only
  description: Only internally sourced documents
  condition:
    field: metadata.source
    operator: in
    value: [internal, proprietary]
    source: documents
    document_match: all
```

Exclude web content:

```yaml
- name: no_web_content
  description: Exclude documents from web sources
  condition:
    field: metadata.source
    operator: not_equals
    value: public-web
    source: documents
    document_match: all
```

### Sensitivity Filters

For high-value users:

```yaml
- name: premium_access
  description: Premium users get broader document access
  condition:
    field: metadata.sensitivity
    operator: lte
    value: 5
    source: documents
    document_match: all
```

## Applying Filters

Filters are applied in organizations:

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

Multiple filters can be combined (all must pass):

```yaml
document_policy:
  filters:
    - enterprise_only        # Must be enterprise tier
    - internal_only          # Must be internal source
    - exclude_confidential   # Cannot be confidential
```

## Filter Resolution

When retrieving documents:

1. Perform vector search
2. For each retrieved document, apply filters:
   - Check each filter condition
   - If ALL filters pass, include document
   - If ANY filter fails, exclude document
3. Return filtered results

## Complex Filtering Scenarios

### Multi-tier Access

```yaml
filters:
  - name: basic_tier
    condition:
      field: metadata.required_tier
      operator: in
      value: [basic, standard, enterprise]
      source: documents
      document_match: all

  - name: enterprise_tier
    condition:
      field: metadata.required_tier
      operator: in
      value: [enterprise]
      source: documents
      document_match: all

orgs:
  - org_id: basic_customer
    document_policy:
      filters: [basic_tier]

  - org_id: enterprise_customer
    document_policy:
      filters: [enterprise_tier]
```

### Time-based Filters

```yaml
- name: recent_documents
  description: Only documents updated in last 30 days
  condition:
    field: metadata.updated_at
    operator: gte
    value: "2026-02-02"
    source: documents
    document_match: all
```

## Best Practices

1. **Start Permissive**: Begin with minimal filtering, add restrictions as needed
2. **Use Consistent Field Names**: Standardize metadata field names
3. **Test Filters**: Verify filters work with your document store
4. **Document Filters**: Use descriptions to explain the purpose
5. **Monitor Results**: Track what documents users retrieve

## See Also

- [Core Concepts Overview](/concepts/overview)
- [Governance](/concepts/governance)
- [Configuration Guide](/getting-started/configuration)
