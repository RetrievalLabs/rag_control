---
title: Governance API Reference
description: Governance and organizations API documentation
---

# Governance API Reference

For detailed information about governance and organizations, see the [Governance](/concepts/governance) concept documentation.

## Key Classes

### Organization

```python
@dataclass
class Organization:
    org_id: str
    description: str
    default_policy: str
    document_policy: DocumentPolicy
    policy_rules: list[PolicyRule]
```

### DocumentPolicy

```python
@dataclass
class DocumentPolicy:
    top_k: int
    filters: list[str]
```

### PolicyRule

```python
@dataclass
class PolicyRule:
    name: str
    description: str
    priority: int
    effect: str  # deny or enforce
    when: RuleCondition
    policy: Optional[str] = None  # For enforce effect
```

### RuleCondition

```python
@dataclass
class RuleCondition:
    all: Optional[list[Condition]] = None  # AND conditions
    any: Optional[list[Condition]] = None  # OR conditions

@dataclass
class Condition:
    field: str
    operator: str  # equals, contains, in, etc.
    value: Any
    source: str  # user or documents
    document_match: Optional[str] = None  # any or all
```

## Registry API

### GovernanceRegistry

```python
class GovernanceRegistry:
    def get_organization(self, org_id: str) -> Organization:
        """Get organization by ID."""

    def get_policy_rules(self, org_id: str) -> list[PolicyRule]:
        """Get policy rules for organization."""

    def resolve_policy(
        self,
        org_id: str,
        user_context: UserContext,
        documents: list[Document],
    ) -> ResolvedPolicy:
        """Resolve which policy applies."""

    def get_default_policy(self, org_id: str) -> str:
        """Get default policy for organization."""
```

## Configuration

Organizations are defined in YAML:

```yaml
orgs:
  - org_id: acme_corp
    description: Acme Corporation
    default_policy: strict_citations
    document_policy:
      top_k: 8
      filters: [enterprise_only]
    policy_rules:
      - name: enterprise_strict
        description: Force strict for enterprise
        priority: 100
        effect: enforce
        when:
          all:
            - field: org_tier
              operator: equals
              value: enterprise
              source: user
        policy: strict_citations
```

## See Also

- [Governance Concept Guide](/concepts/governance)
- [Configuration Guide](/getting-started/configuration)
- [Engine API](/api/engine)
