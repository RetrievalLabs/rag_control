---
title: Policies API Reference
description: Policy-related API documentation
---

# Policies API Reference

For detailed information about policies and their configuration, see the [Policies](/concepts/policies) concept documentation.

## Key Classes

### Policy

```python
@dataclass
class Policy:
    name: str
    description: str
    generation: GenerationConfig
    enforcement: EnforcementConfig
    logging: LoggingConfig
```

### GenerationConfig

```python
@dataclass
class GenerationConfig:
    reasoning_level: str  # limited, moderate, full
    allow_external_knowledge: bool
    require_citations: bool
    temperature: float  # 0.0 to 2.0
    max_output_tokens: int
```

### EnforcementConfig

```python
@dataclass
class EnforcementConfig:
    validate_citations: bool
    block_on_missing_citations: bool
    prevent_external_knowledge: bool
```

### LoggingConfig

```python
@dataclass
class LoggingConfig:
    level: str  # full, minimal, none
```

## Registry API

### PolicyRegistry

```python
class PolicyRegistry:
    def get_policy(self, policy_name: str) -> Policy:
        """Get policy by name."""

    def validate_policy(self, policy: Policy) -> bool:
        """Validate policy configuration."""

    def get_all_policies(self) -> list[Policy]:
        """Get all configured policies."""
```

## Configuration

Policies are defined in YAML:

```yaml
policies:
  - name: strict_citations
    description: Strict policy with citations
    generation:
      reasoning_level: limited
      allow_external_knowledge: false
      require_citations: true
      temperature: 0.0
      max_output_tokens: 512
    enforcement:
      validate_citations: true
      block_on_missing_citations: true
      prevent_external_knowledge: true
    logging:
      level: full
```

## See Also

- [Policies Concept Guide](/concepts/policies)
- [Configuration Guide](/getting-started/configuration)
- [Engine API](/api/engine)
