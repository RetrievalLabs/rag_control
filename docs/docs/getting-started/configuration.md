---
title: Configuration Guide
description: Comprehensive guide to configuring rag_control
---

# Configuration Guide

rag_control is configured using YAML files that define policies, governance rules, filters, and organizations.

## Configuration Structure

```yaml
policies:
  # Policy definitions
  - name: policy_name
    # ... policy config

filters:
  # Filter definitions
  - name: filter_name
    # ... filter config

orgs:
  # Organization definitions
  - org_id: org_id
    # ... org config

```

## Policies

Policies control LLM generation behavior and enforce constraints.

### Policy Fields

```yaml
policies:
  - name: strict_citations
    description: Strict policy requiring citations

    generation:
      # Control LLM generation
      reasoning_level: limited  # none, limited, or full
      allow_external_knowledge: false
      require_citations: true
      fallback: strict          # strict or soft
      temperature: 0.0          # 0.0 to 2.0

    enforcement:
      # Runtime enforcement checks
      validate_citations: true
      block_on_missing_citations: true
      enforce_strict_fallback: true
      prevent_external_knowledge: true
      max_output_tokens: 512

    logging:
      # Audit logging level
      level: full               # full or minimal
```

### Generation Parameters

| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| `reasoning_level` | string | `none`, `limited`, `full` | `limited` | Controls how much reasoning the LLM shows: **none** = no reasoning, **limited** = brief steps, **full** = detailed reasoning |
| `allow_external_knowledge` | boolean | `true` or `false` | `false` | Whether LLM can use knowledge beyond retrieved documents |
| `require_citations` | boolean | `true` or `false` | `true` | Whether LLM must include citations for claims |
| `fallback` | string | `strict` or `soft` | `strict` | **strict** = fail if constraints can't be satisfied, **soft** = relax constraints gracefully |
| `temperature` | float | 0.0 - 2.0 | `0.0` | Response creativity: 0.0 = deterministic, 2.0 = creative |

### Enforcement Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validate_citations` | boolean | `true` | Verify citations actually exist in retrieved documents |
| `block_on_missing_citations` | boolean | `true` | Block response if citations are missing |
| `enforce_strict_fallback` | boolean | `true` | Enforce the fallback strategy (`strict` or `soft`) at runtime |
| `prevent_external_knowledge` | boolean | `true` | Block responses with claims not in retrieved documents |
| `max_output_tokens` | integer or null | `null` | Maximum tokens in response; `null` = no limit |

> **Learn more:** See [Policies](/concepts/policies) concept guide for detailed policy behavior and examples.

## Filters

Filters control document retrieval based on data classification and metadata.

### Filter Definition

```yaml
filters:
  - name: enterprise_only
    condition:
      field: org_tier              # User field to check
      operator: equals             # equals, contains, in, etc.
      value: enterprise            # Expected value
      source: user                 # user or documents

  - name: public_documents_only
    condition:
      field: metadata.classification
      operator: equals
      value: public
      source: documents
      document_match: any          # any or all
```

### Filter Operators

| Operator | Supported Values | Description |
|----------|------------------|-------------|
| `equals` | Any | Exact match of field value |
| `in` | List | Field value is in provided list |
| `lt` | Number | Field value is less than |
| `lte` | Number | Field value is less than or equal to |
| `gt` | Number | Field value is greater than |
| `gte` | Number | Field value is greater than or equal to |
| `intersects` | List | Field array intersects with provided list |
| `exists` | N/A | Field exists (no value needed) |

### Filter Sources

| Source | Description |
|--------|-------------|
| `user` | Check fields from user context or request metadata |
| `documents` | Check fields from retrieved documents. Use with `document_match` |

### Filter Logic

Filters support nested AND/OR logic:

```yaml
filters:
  - name: complex_filter
    or:
      - and:
          - condition:
              field: metadata.classification
              operator: equals
              value: public
              source: documents
          - condition:
              field: metadata.retention_days
              operator: gte
              value: 365
              source: documents
      - condition:
          field: user_role
          operator: in
          value: [admin, analyst]
          source: user
```

> **Learn more:** See [Filters](/concepts/filters) concept guide for advanced filter patterns and use cases.

## Document Policy

Document policies control document retrieval behavior for organizations.

### Document Policy Definition

```yaml
document_policy:
  top_k: 5                    # Number of documents to retrieve (required, must be > 0)
  filter_name: null           # Optional: filter to apply to document retrieval
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_k` | integer | `5` | Number of documents to retrieve. Must be greater than 0 |
| `filter_name` | string or null | `null` | Optional filter name to apply to document retrieval. Must exist in filters section |

> **Learn more:** See [Document Retrieval](/concepts/retrieval) concept guide for information about document selection and ranking.

## Policy Rules

Policy rules enable dynamic policy selection and request blocking based on conditions.

### Policy Rule Definition

```yaml
policy_rules:
  - name: rule_name
    description: Rule description
    priority: 100                    # Higher = evaluated first (must be unique, > 0)
    effect: allow                    # allow or deny
    apply_policy: policy_name        # (optional) Policy to apply when rule matches
    when:
      all:                           # All conditions must match (AND logic)
        - field: field_name
          operator: equals           # equals, lt, lte, gt, gte, intersects, exists
          value: some_value          # (not needed for 'exists')
          source: user               # user or documents
          document_match: any        # any or all (documents only)
```

### Policy Rule Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Unique name for the rule |
| `description` | string | No | Human-readable description |
| `priority` | integer | Yes | Evaluation order: higher = first. Must be unique and > 0 |
| `effect` | string | Yes | `allow` (permit) or `deny` (block) |
| `apply_policy` | string | No | Policy to apply when rule matches. Used with `allow` effect |
| `when` | object | Yes | Conditions that trigger the rule |

### Rule Condition Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `field` | string | Field to check (supports dot notation: `metadata.classification`) |
| `operator` | string | Comparison operator (see Rule Operators below) |
| `value` | any | Expected value. Not needed for `exists` operator |
| `source` | string | `user` (context fields) or `documents` (document metadata) |
| `document_match` | string | `any` (match any doc) or `all` (match all docs). Only for `documents` source |

### Rule Operators

| Operator | Supported Values | Description |
|----------|------------------|-------------|
| `equals` | Any | Exact match |
| `lt` | Number | Less than |
| `lte` | Number | Less than or equal to |
| `gt` | Number | Greater than |
| `gte` | Number | Greater than or equal to |
| `intersects` | List | Field array intersects with provided list |
| `exists` | N/A | Field exists (no value needed) |

### Rule Evaluation

- Rules are evaluated in **priority order** (highest first)
- First matching rule determines the action
- All conditions in `all` must be true (AND)
- Any condition in `any` can be true (OR)
- Use `document_match: any` when applying conditions to documents (matches if any doc meets the condition)
- Use `document_match: all` to require all documents to meet the condition

> **Learn more:** See [Governance](/concepts/governance) concept guide for policy rule strategies and enforcement patterns.

## Organizations

Organizations apply organization-specific rules and settings.

### Organization Definition

```yaml
orgs:
  - org_id: acme_corp
    description: Acme Corporation
    default_policy: strict_citations

    # Document retrieval settings
    document_policy:
      top_k: 8                      # Number of documents to retrieve
      filter_name: enterprise_only  # Optional: filter applied to all requests

    # Policy rules for organization-specific governance
    policy_rules: []                # Can be empty if no additional rules needed
```

### Organization Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `org_id` | string | Yes | Unique organization identifier |
| `description` | string | No | Human-readable organization description |
| `default_policy` | string | Yes | Default policy name (must exist in policies) |
| `document_policy` | object | Yes | Document retrieval configuration (see Document Policy section) |
| `policy_rules` | list | Yes | List of policy rules (can be empty) |

### Example Organization Structure

```yaml
orgs:
  - org_id: acme_corp
    description: Acme Corporation
    default_policy: strict_citations

    # Document retrieval settings
    document_policy:
      top_k: 5

    # Organization-specific policy rules
    policy_rules:
      - name: deny_untrusted_sources
        description: Deny untrusted sources
        priority: 60                # Higher priority = evaluated first
        effect: deny                # deny to block, allow to permit
        when:
          any:                      # Match any condition
            - field: metadata.source
              operator: equals
              value: public-web
              source: documents
              document_match: any

      - name: apply_strict_citations
        description: Apply strict citations policy
        priority: 50
        effect: allow
        apply_policy: strict_citations
        when:
          all:                      # Match all conditions
            - field: org_tier
              operator: equals
              value: enterprise
              source: user
```

### Rule Effects

| Effect | Description |
|--------|-------------|
| `deny` | Block the request with a denial error. Stops processing immediately |
| `allow` | Permit the request. If `apply_policy` specified, apply that policy |

### Rule Conditions

Rules use `when` clauses with:

- `any`: Match if any condition is true (OR)
- `all`: Match if all conditions are true (AND)

> **Learn more:** See [Organizations](/concepts/organizations) concept guide for multi-tenant setup and organization management.

## Example Configurations

### Development Configuration

```yaml
policies:
  - name: development
    description: Permissive development environment
    generation:
      reasoning_level: full
      allow_external_knowledge: true
      require_citations: false
      fallback: soft
      temperature: 0.7
    enforcement:
      validate_citations: false
      block_on_missing_citations: false
      enforce_strict_fallback: false
      prevent_external_knowledge: false
      max_output_tokens: 2048
    logging:
      level: full

orgs:
  - org_id: dev
    description: Development organization
    default_policy: development
    document_policy:
      top_k: 10
    policy_rules: []
```

### Production Configuration

```yaml
policies:
  - name: production
    generation:
      reasoning_level: limited
      allow_external_knowledge: false
      require_citations: true
      temperature: 0.1
    enforcement:
      validate_citations: true
      block_on_missing_citations: true
      enforce_strict_fallback: true
      prevent_external_knowledge: true
      max_output_tokens: 512
    logging:
      level: full

filters:
  - name: sensitive_only
    condition:
      field: metadata.classification
      operator: in
      value: [sensitive, confidential]
      source: documents

orgs:
  - org_id: production
    default_policy: production
    document_policy:
      top_k: 5
      filter_name: sensitive_only
    policy_rules:
      - name: block_external_knowledge
        priority: 100
        effect: deny
        when:
          all:
            - field: metadata.is_external
              operator: equals
              value: true
              source: documents
              document_match: any
```

### Multi-Organization Setup

```yaml
policies:
  - name: strict
    # ... strict config

  - name: moderate
    # ... moderate config

filters:
  - name: acme_filter
    # ... acme-specific filter

orgs:
  - org_id: acme_corp
    default_policy: strict
    document_policy:
      top_k: 5
      filter_name: acme_filter
    policy_rules:
      - name: acme_specific_rule
        priority: 50
        effect: allow
        apply_policy: strict
        when:
          all:
            - field: org_id
              operator: equals
              value: acme_corp
              source: user

  - org_id: standard_org
    default_policy: moderate
    document_policy:
      top_k: 10
```

## Validation

rag_control validates configurations on startup:

```python
from rag_control.core.engine import RAGControl

try:
    engine = RAGControl(
        llm=llm_adapter,
        query_embedding=embedding_adapter,
        vector_store=vector_store_adapter,
        config_path="policy_config.yaml"
    )
except Exception as e:
    print(f"Configuration error: {e}")
```

## Configuration Best Practices

1. **Start Simple**: Begin with one policy and one organization
2. **Use Meaningful Names**: Policy and filter names should describe their purpose
3. **Document Rules**: Use descriptions for all rules and policies
4. **Test Thoroughly**: Verify policies work with your adapters
5. **Version Control**: Keep configurations in git
6. **Separate Environments**: Use different configs for dev, staging, production

## Configuration Reference

The control plane configuration is fully documented in the [Configuration Guide](/getting-started/configuration).

## Next Steps

- Understand [Core Concepts](/concepts/overview)
- Explore [Policies](/concepts/policies) in detail
- Learn about [Governance](/concepts/governance)
- Check the [API Reference](/api/engine)
