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
      reasoning_level: limited  # limited, moderate, full
      allow_external_knowledge: false
      require_citations: true
      temperature: 0.0          # 0.0 to 2.0
      max_output_tokens: 512

    enforcement:
      # Runtime enforcement checks
      validate_citations: true
      block_on_missing_citations: true
      prevent_external_knowledge: true

    logging:
      # Audit logging level
      level: full               # full, minimal, none
```

### Generation Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `reasoning_level` | string | `limited`, `moderate`, or `full` | `moderate` |
| `allow_external_knowledge` | boolean | Allow knowledge outside retrieved documents | `false` |
| `require_citations` | boolean | Require citations for claims | `false` |
| `temperature` | float | 0.0 to 2.0, higher = more creative | `0.7` |
| `max_output_tokens` | integer | Maximum response length | `1024` |

### Enforcement Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `validate_citations` | boolean | Verify citations match documents |
| `block_on_missing_citations` | boolean | Block response if citations missing |
| `prevent_external_knowledge` | boolean | Block claims without document support |

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

### Operators

- `equals`: Exact match
- `contains`: String contains substring
- `in`: Value in list
- `not_equals`: Not equal
- `not_contains`: Does not contain

### Filter Sources

- `user`: Check user context fields
- `documents`: Check document metadata

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
      filters: [enterprise_only]    # Applied filters

    # Organization-specific policy rules
    policy_rules:
      - name: deny_untrusted_sources
        description: Deny untrusted sources
        priority: 60                # Higher = evaluated first
        effect: deny                # deny or enforce
        when:
          any:                      # Match any condition
            - field: metadata.source
              operator: equals
              value: public-web
              source: documents
              document_match: any

      - name: enforce_citations
        description: Enforce strict citations
        priority: 50
        effect: enforce
        when:
          all:                      # Match all conditions
            - field: org_tier
              operator: equals
              value: enterprise
              source: user
        policy: strict_citations
```

### Rule Effects

- `deny`: Block the request with a denial error
- `enforce`: Apply the specified policy

### Rule Conditions

Rules use `when` clauses with:

- `any`: Match if any condition is true (OR)
- `all`: Match if all conditions are true (AND)

## Example Configurations

### Development Configuration

```yaml
policies:
  - name: development
    generation:
      reasoning_level: full
      allow_external_knowledge: true
      require_citations: false
      temperature: 0.7
      max_output_tokens: 2048
    enforcement:
      validate_citations: false
      block_on_missing_citations: false
      prevent_external_knowledge: false

orgs:
  - org_id: dev
    default_policy: development
    document_policy:
      top_k: 10
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
      max_output_tokens: 512
    enforcement:
      validate_citations: true
      block_on_missing_citations: true
      prevent_external_knowledge: true
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
      filters: [sensitive_only]
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
    policy_rules:
      - name: acme_specific_rule
        priority: 50
        effect: enforce
        when:
          all:
            - field: org_id
              operator: equals
              value: acme_corp
              source: user
        policy: strict

  - org_id: standard_org
    default_policy: moderate
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

For detailed specification, see the [Control Plane Config Contract](/specs/config-contract)

## Next Steps

- Understand [Core Concepts](/concepts/overview)
- Explore [Policies](/concepts/policies) in detail
- Learn about [Governance](/concepts/governance)
- Check the [API Reference](/api/engine)
