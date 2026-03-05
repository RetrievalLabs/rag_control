---
title: Policy, Governance & Filters API Reference
description: Creating policies, governance configs, and filters with Python models
---

# Policy, Governance & Filters API Reference

Configure policies, governance rules, and document filters using Python models from `rag_control.models`.

## Policy Models

Create policies by composing `GenerationPolicy`, `LoggingPolicy`, and `EnforcementPolicy` into a `Policy` object.

### Policy

```python
from rag_control.models.policy import (
    Policy,
    GenerationPolicy,
    LoggingPolicy,
    EnforcementPolicy,
)

policy = Policy(
    name="strict-policy",
    description="Strict policy for sensitive queries",
    generation=GenerationPolicy(
        reasoning_level="full",
        allow_external_knowledge=False,
        require_citations=True,
        fallback="strict",
        temperature=0.0,
    ),
    logging=LoggingPolicy(level="full"),
    enforcement=EnforcementPolicy(
        validate_citations=True,
        block_on_missing_citations=True,
        enforce_strict_fallback=True,
        prevent_external_knowledge=True,
        max_output_tokens=1000,
    ),
)
```

### GenerationPolicy

Controls how the LLM generates responses.

- `reasoning_level: Literal["none", "limited", "full"]` - Depth of reasoning (default: "limited")
- `allow_external_knowledge: bool` - Allow knowledge beyond training data (default: False)
- `require_citations: bool` - Require citations for all claims (default: True)
- `fallback: Literal["strict", "soft"]` - Fallback behavior when constraints violated (default: "strict")
- `temperature: float` - Generation temperature (default: 0.0)

### LoggingPolicy

Controls logging verbosity.

- `level: Literal["minimal", "full"]` - Logging detail level (default: "full")

### EnforcementPolicy

Controls enforcement of generation constraints.

- `validate_citations: bool` - Validate citation correctness (default: True)
- `block_on_missing_citations: bool` - Block response if citations missing (default: True)
- `enforce_strict_fallback: bool` - Enforce strict fallback mode (default: True)
- `prevent_external_knowledge: bool` - Prevent external knowledge usage (default: True)
- `max_output_tokens: int | None` - Maximum output tokens (default: None)

---

## Governance Models

Create governance configurations for organizations using `PolicyRule` and `OrgConfig`.

### PolicyRule

Defines a policy routing rule.

```python
from rag_control.models.rule import PolicyRule, LogicalCondition, Condition

rule = PolicyRule(
    name="high-risk-users",
    description="Apply strict policy for high-risk users",
    priority=1,
    effect="allow",
    apply_policy="strict-policy",
    when=LogicalCondition(
        any=[
            Condition(
                field="user_tier",
                operator="equals",
                value="high_risk",
                source="user",
            ),
        ],
    ),
)
```

**Fields:**
- `name: str` - Rule name
- `description: str | None` - Optional description
- `priority: int` - Rule priority (evaluated in order)
- `effect: Literal["allow", "deny"]` - Allow or deny when conditions match
- `apply_policy: str | None` - Policy to apply on allow effect
- `when: LogicalCondition` - Conditions for matching

### LogicalCondition

Combines conditions with AND/OR logic.

```python
from rag_control.models.rule import LogicalCondition, Condition

condition = LogicalCondition(
    all=[
        Condition(field="user_level", operator="gte", value=3, source="user"),
        Condition(field="category", operator="in", value=["finance", "health"], source="documents"),
    ],
)
```

**Fields:**
- `all: List[Condition] | None` - All conditions must match (AND)
- `any: List[Condition] | None` - Any condition must match (OR)

### Condition

Defines a single matching condition.

```python
from rag_control.models.rule import Condition

condition = Condition(
    field="user_tier",
    operator="equals",
    value="premium",
    source="user",
    document_match=None,
)
```

**Fields:**
- `field: str` - Field to evaluate
- `operator: Literal["equals", "lt", "lte", "gt", "gte", "intersects", "exists"]` - Comparison operator
- `value: str | int | float | None` - Value to compare (None for "exists")
- `source: Literal["user", "documents"]` - Source of field (default: "user")
- `document_match: Literal["any", "all"] | None` - Match strategy for document fields

### OrgConfig

Organization-level governance configuration.

```python
from rag_control.models.org import OrgConfig, DocumentPolicy

org_config = OrgConfig(
    org_id="acme-corp",
    description="ACME Corporation governance",
    default_policy="standard-policy",
    policy_rules=[rule1, rule2, rule3],
    document_policy=DocumentPolicy(
        top_k=10,
        filter_name="public-docs-filter",
    ),
)
```

**Fields:**
- `org_id: str` - Organization ID
- `description: str | None` - Optional description
- `default_policy: str` - Default policy name when no rules match
- `policy_rules: list[PolicyRule]` - List of policy rules
- `document_policy: DocumentPolicy` - Document retrieval settings

### DocumentPolicy

Document retrieval settings for an organization.

- `top_k: int` - Number of documents to retrieve (default: 5)
- `filter_name: str | None` - Filter to apply on retrieval (default: None)

---

## Filter Models

Create document filters using `Condition` and `Filter` models.

### Filter

Hierarchical filter for document matching.

```python
from rag_control.models.filter import Filter, Condition

filter_obj = Filter(
    name="public-docs-filter",
    description="Public documents only",
    and_=[
        Filter(
            name="dept-filter",
            condition=Condition(
                field="department",
                operator="in",
                value=["engineering", "marketing"],
            ),
        ),
        Filter(
            name="status-filter",
            condition=Condition(
                field="status",
                operator="equals",
                value="published",
            ),
        ),
    ],
)
```

**Fields:**
- `name: str` - Filter name
- `description: str | None` - Optional description
- `and_: List[Filter] | None` - Sub-filters combined with AND logic
- `or_: List[Filter] | None` - Sub-filters combined with OR logic
- `condition: Condition | None` - Single condition (leaf node)

### Condition (Filter)

Defines a filter condition.

```python
from rag_control.models.filter import Condition

condition = Condition(
    field="created_date",
    operator="gte",
    value="2024-01-01",
    source="user",
)
```

**Fields:**
- `field: str` - Field to evaluate
- `operator: Literal["equals", "in", "intersects", "lt", "lte", "gt", "gte", "exists"]` - Operator
- `value: str | int | List[str] | List[int] | None` - Value(s) to compare
- `source: Literal["user"]` - Always "user" for filters (default: "user")

**Operators:**
- `equals` - Exact match
- `in` - Value in list
- `intersects` - List intersection
- `lt`, `lte`, `gt`, `gte` - Numeric comparison
- `exists` - Field exists (value should be None)

---

## Complete Example

```python
from rag_control.models.policy import (
    Policy, GenerationPolicy, LoggingPolicy, EnforcementPolicy,
)
from rag_control.models.rule import PolicyRule, LogicalCondition, Condition
from rag_control.models.org import OrgConfig, DocumentPolicy
from rag_control.models.filter import Filter, Condition as FilterCondition

# Create policies
strict_policy = Policy(
    name="strict",
    generation=GenerationPolicy(reasoning_level="full", temperature=0.0),
    logging=LoggingPolicy(level="full"),
    enforcement=EnforcementPolicy(max_output_tokens=500),
)

balanced_policy = Policy(
    name="balanced",
    generation=GenerationPolicy(reasoning_level="limited", temperature=0.5),
    logging=LoggingPolicy(level="minimal"),
    enforcement=EnforcementPolicy(max_output_tokens=2000),
)

# Create filters
public_filter = Filter(
    name="public-docs",
    and_=[
        Filter(
            condition=FilterCondition(
                field="visibility",
                operator="equals",
                value="public",
            ),
        ),
    ],
)

# Create policy rules
admin_rule = PolicyRule(
    name="admin-rule",
    priority=1,
    effect="allow",
    apply_policy="strict",
    when=LogicalCondition(
        all=[
            Condition(field="role", operator="equals", value="admin", source="user"),
        ],
    ),
)

default_rule = PolicyRule(
    name="default-rule",
    priority=100,
    effect="allow",
    apply_policy="balanced",
    when=LogicalCondition(any=[]),
)

# Create org config
org_config = OrgConfig(
    org_id="myorg",
    default_policy="balanced",
    policy_rules=[admin_rule, default_rule],
    document_policy=DocumentPolicy(top_k=10, filter_name="public-docs"),
)
```

---

## ControlPlaneConfig

The complete configuration passed to the RAGControl engine.

```python
from rag_control.models.config import ControlPlaneConfig
```

**Fields:**
- `policies: list[Policy]` - All policies
- `filters: list[Filter]` - All filters
- `orgs: list[OrgConfig]` - All organization configurations

### Complete Configuration Example

```python
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.policy import (
    Policy, GenerationPolicy, LoggingPolicy, EnforcementPolicy,
)
from rag_control.models.rule import PolicyRule, LogicalCondition, Condition
from rag_control.models.org import OrgConfig, DocumentPolicy
from rag_control.models.filter import Filter, Condition as FilterCondition
from rag_control.core.engine import RAGControlEngine
from rag_control.adapters import LLM, QueryEmbedding, VectorStore

# Create policies
policies = [
    Policy(
        name="strict",
        description="For admin users",
        generation=GenerationPolicy(
            reasoning_level="full",
            allow_external_knowledge=False,
            require_citations=True,
            fallback="strict",
            temperature=0.0,
        ),
        logging=LoggingPolicy(level="full"),
        enforcement=EnforcementPolicy(
            validate_citations=True,
            block_on_missing_citations=True,
            max_output_tokens=500,
        ),
    ),
    Policy(
        name="balanced",
        description="For regular users",
        generation=GenerationPolicy(
            reasoning_level="limited",
            allow_external_knowledge=False,
            require_citations=True,
            fallback="soft",
            temperature=0.5,
        ),
        logging=LoggingPolicy(level="minimal"),
        enforcement=EnforcementPolicy(max_output_tokens=2000),
    ),
]

# Create filters
filters = [
    Filter(
        name="public-docs",
        description="Public documents only",
        condition=FilterCondition(
            field="visibility",
            operator="equals",
            value="public",
        ),
    ),
]

# Create organization configurations
orgs = [
    OrgConfig(
        org_id="acme-corp",
        description="ACME Corporation",
        default_policy="balanced",
        policy_rules=[
            PolicyRule(
                name="admin-rule",
                priority=1,
                effect="allow",
                apply_policy="strict",
                when=LogicalCondition(
                    all=[
                        Condition(
                            field="role",
                            operator="equals",
                            value="admin",
                            source="user",
                        ),
                    ],
                ),
            ),
        ],
        document_policy=DocumentPolicy(top_k=10, filter_name="public-docs"),
    ),
]

# Create control plane config
config = ControlPlaneConfig(
    policies=policies,
    filters=filters,
    orgs=orgs,
)

# Initialize RAGControl engine with config
engine = RAGControlEngine(
    llm=your_llm_adapter,
    query_embedding=your_embedding_adapter,
    vector_store=your_vector_store_adapter,
    config=config,
)
```

### Configuration Validation

The `ControlPlaneConfig` validates:
- Policy names are unique
- Filter names are unique
- Org IDs are unique
- Referenced policies exist
- Referenced filters exist
- Rule priorities are unique and positive
- Filter structure is valid (exactly one of: condition, and, or)
- All constraints are satisfied

Invalid configs raise `ControlPlaneConfigValidationError`.

---

## YAML Configuration Alternative

Configs can also be loaded from YAML files 

For YAML structure and configuration details, see the [Configuration Guide](/guides/configuration).

## See Also

- [Engine API](/api/engine)
- [Exceptions API](/api/exceptions)
- [Governance Concept Guide](/concepts/governance)
