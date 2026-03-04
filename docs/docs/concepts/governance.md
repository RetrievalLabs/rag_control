---
title: Governance
description: Understanding rag_control governance and security
---

# Governance

Governance in rag_control provides organization-level control over policy enforcement, access, and security.

## What is Governance?

Governance is the set of rules that apply at the organization level:

- Which policies apply to which requests
- Organization-specific overrides and rules
- Role-based access control
- Data classification and sensitivity

## Organizations

Organizations are the fundamental unit of governance:

```yaml
orgs:
  - org_id: acme_corp
    description: Acme Corporation
    default_policy: strict_citations
    document_policy:
      top_k: 8
      filters: [enterprise_only]
    policy_rules:
      # Organization-specific rules
```

### Organization Fields

| Field | Type | Description |
|-------|------|-------------|
| `org_id` | string | Unique organization identifier |
| `description` | string | Human-readable description |
| `default_policy` | string | Policy used if no rule matches |
| `document_policy` | object | Document retrieval settings |
| `policy_rules` | array | Organization-specific policy rules |

## Policy Rules

Policy rules determine which policy to apply based on conditions:

### Rule Structure

```yaml
policy_rules:
  - name: rule_name
    description: What this rule does
    priority: 60              # Higher priority = evaluated first
    effect: enforce           # deny or enforce
    when:
      all:                    # Match all conditions
        - field: org_tier
          operator: equals
          value: enterprise
          source: user
    policy: strict_citations  # Policy to apply
```

### Rule Effects

**enforce**: Apply a specific policy

```yaml
- name: enforce_strict_for_enterprise
  priority: 50
  effect: enforce
  when:
    all:
      - field: org_tier
        operator: equals
        value: enterprise
        source: user
  policy: strict_citations
```

**deny**: Block the request entirely

```yaml
- name: deny_untrusted_sources
  priority: 60
  effect: deny
  when:
    any:
      - field: metadata.source
        operator: equals
        value: untrusted
        source: documents
        document_match: any
```

## Rule Conditions

Rules use `when` clauses with conditions:

### Condition Structure

```yaml
when:
  all:                          # all or any
    - field: user.org_tier
      operator: equals
      value: enterprise
      source: user              # user or documents
      document_match: any       # any or all (documents only)
```

### Operators

- `equals`: Exact match
- `contains`: String contains
- `in`: Value in list
- `not_equals`: Not equal
- `not_contains`: Does not contain

### Sources

- **user**: User context fields (org_id, user_id, org_tier, etc.)
- **documents**: Document metadata from retrieval

### Document Matching

When source is "documents":

- `any`: Match if any document matches condition
- `all`: Match only if all documents match condition

## Examples

### Enterprise Policy Override

Enforce strict policy for enterprise customers:

```yaml
- name: enterprise_strict
  description: Force strict policy for enterprise orgs
  priority: 100
  effect: enforce
  when:
    all:
      - field: org_id
        operator: equals
        value: enterprise_acme
        source: user
      - field: org_tier
        operator: equals
        value: enterprise
        source: user
  policy: strict_citations
```

### Sensitive Document Handling

Apply strict policy if sensitive documents are retrieved:

```yaml
- name: sensitive_document_strict
  description: Use strict policy when sensitive docs are retrieved
  priority: 80
  effect: enforce
  when:
    any:
      - field: metadata.classification
        operator: in
        value: [sensitive, confidential]
        source: documents
        document_match: any
  policy: strict_citations
```

### Deny Untrusted Sources

Block entirely if untrusted source documents are retrieved:

```yaml
- name: deny_untrusted
  description: Deny if untrusted sources in results
  priority: 90
  effect: deny
  when:
    any:
      - field: metadata.source
        operator: equals
        value: public-web
        source: documents
        document_match: any
```

### Research vs Production

Different policies for different environments:

```yaml
orgs:
  - org_id: research_team
    default_policy: exploratory
    policy_rules:
      - name: research_override
        priority: 10
        effect: enforce
        when:
          all:
            - field: environment
              operator: equals
              value: development
              source: user
        policy: exploratory

  - org_id: production_team
    default_policy: strict_citations
    policy_rules:
      - name: production_strict
        priority: 10
        effect: enforce
        when:
          all:
            - field: environment
              operator: equals
              value: production
              source: user
        policy: strict_citations
```

## Rule Priority

Rules are evaluated in order of priority (highest first):

```yaml
policy_rules:
  - name: critical_rule
    priority: 100    # Evaluated first
    effect: deny

  - name: standard_rule
    priority: 50     # Evaluated second

  - name: fallback_rule
    priority: 10     # Evaluated last
```

## User Context

User context is passed with each request:

```python
from rag_control.models.user import UserContext

user_context = UserContext(
    org_id="acme_corp",      # Organization ID
    user_id="user-123",      # User ID
    org_tier="enterprise",   # Organization tier
    role="analyst",          # User role (optional)
    # Additional custom fields
)
```

Governance rules can check any field in user context.

## Execution Flow

When a request comes in:

1. **Validate Organization**: Check user's org_id
2. **Evaluate Rules**: Check policy_rules in priority order
3. **Stop on Match**: First matching rule applies
4. **Apply Policy**: Use rule's policy or deny request
5. **Use Default**: If no rule matches, use default_policy

## Best Practices

1. **Clear Priorities**: Use consistent priority ranges (10, 50, 100)
2. **Specific Rules First**: Higher priority for more specific conditions
3. **Test Conditions**: Verify conditions work with your data
4. **Document Rules**: Use descriptions for compliance
5. **Audit Changes**: Track governance rule changes

## See Also

- [Core Concepts Overview](/concepts/overview)
- [Policies](/concepts/policies)
- [Configuration Guide](/getting-started/configuration)
