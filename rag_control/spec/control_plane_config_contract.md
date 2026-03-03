Control Plane Config Contract

Version: v2026.1
Status: Draft
Applies To:
- `rag_control.models.config.ControlPlaneConfig`
- `rag_control.models.org.OrgConfig`
- `rag_control.models.policy.Policy`
- `rag_control.models.rule.PolicyRule`
- `rag_control.models.filter.Filter`

Purpose
- Define the required schema and validation behavior for control-plane configuration.
- Ensure policy/filter/rule references are consistent and resolvable at runtime.

Normative Terms
- MUST: required.
- SHOULD: recommended unless system constraints prevent it.
- MAY: optional.

Top-Level Model: `ControlPlaneConfig`
- Fields:
  - `policies: list[Policy]`
  - `filters: list[Filter]`
  - `orgs: list[OrgConfig]`
- Validation invariants:
  - `policies[*].name` MUST be unique.
  - `filters[*].name` MUST be unique.
  - `orgs[*].org_id` MUST be unique.
  - Every `org.default_policy` MUST reference an existing `policies[*].name`.
  - If present, every `org.filter_name` MUST reference an existing `filters[*].name`.
  - Within each org:
    - `policy_rules[*].name` MUST be unique.
    - `policy_rules[*].priority` MUST be unique.
    - `policy_rules[*].priority` MUST be greater than `0`.
    - If present, `policy_rules[*].apply_policy` MUST reference an existing `policies[*].name`.
- Errors:
  - Violations MUST raise `ControlPlaneConfigValidationError`.

Org Model: `OrgConfig`
- Fields:
  - `org_id: str` (required)
  - `description: str | None` (optional)
  - `default_policy: str` (required)
  - `policy_rules: list[PolicyRule]` (required)
  - `filter_name: str | None` (optional)
  - `document_policy: DocumentPolicy` (optional; default values apply)

Document Policy: `DocumentPolicy`
- `top_k: int` (default `5`, MUST be `> 0`)

Policy Model: `Policy`
- Fields:
  - `name: str` (required)
  - `description: str | None` (optional)
  - `generation: GenerationPolicy` (required)
  - `logging: LoggingPolicy` (required)
  - `enforcement: EnforcementPolicy` (required)

Generation Policy: `GenerationPolicy`
- `reasoning_level`: one of `none | limited | full` (default `limited`)
- `allow_external_knowledge: bool` (default `false`)
- `require_citations: bool` (default `true`)
- `fallback`: one of `strict | soft` (default `strict`)
- `temperature: float` (default `0.0`)

Logging Policy: `LoggingPolicy`
- `level`: one of `minimal | full` (default `full`)

Enforcement Policy: `EnforcementPolicy`
- `validate_citations: bool` (default `true`)
- `block_on_missing_citations: bool` (default `true`)
- `enforce_strict_fallback: bool` (default `true`)
- `prevent_external_knowledge: bool` (default `true`)
- `max_output_tokens: int | None` (default `None`)

Policy Rule Model: `PolicyRule`
- Fields:
  - `name: str` (required)
  - `description: str | None` (optional)
  - `priority: int` (required, and MUST be `> 0` by config-level validation)
  - `effect`: one of `allow | deny` (required)
  - `apply_policy: str | None` (optional, if set MUST reference existing `Policy.name`)
  - `when: LogicalCondition` (required)

Policy Rule Condition Models
- `LogicalCondition`
  - `all: list[Condition] | None`
  - `any: list[Condition] | None`
  - Evaluation semantics:
    - If only `all` is present, all listed conditions MUST match.
    - If only `any` is present, at least one listed condition MUST match.
    - If both `all` and `any` are present, implementations MUST require
      `all` **and** `any` to match.
    - Empty lists SHOULD evaluate as non-match.
- `Condition`
  - `field: str` (required)
  - `operator`: one of `equals | lt | lte | gt | gte | intersects | exists`
  - `value: str | int | None`
  - `source: "user" | "documents" (default "user")`
  - `document_match: "any" | "all" | None` (only valid when `source` is `"documents"`)
  - `field` path resolution behavior:
    - For `source: "user"`, implementations MUST resolve:
      - top-level `UserContext` fields (for example `user_id`, `org_id`)
      - extra custom top-level fields on `UserContext` (for example `profile`)
      - keys under `attributes` both with and without prefix
        (for example `department` and `attributes.department`)
      - nested dot paths (for example `region.status`, `region.status.top`)
    - For `source: "documents"`, implementations MUST resolve nested dot paths
      against retrieved document records (for example `metadata.source`,
      `metadata.region.status`, `metadata.region.status.top`)
    - Missing paths SHOULD evaluate as not matched.

Filter Model: `Filter`
- Fields:
  - `name: str` (required)
  - `description: str | None` (optional)
  - `and` / `and_`: optional list of nested `Filter`
  - `or` / `or_`: optional list of nested `Filter`
  - `condition: FilterCondition | None`
- Node semantics:
  - Each filter node MUST include exactly one of: `condition`, `and`, `or`.
- Input alias behavior:
  - Implementations MUST accept both `and` and `and_`.
  - Implementations MUST accept both `or` and `or_`.

Filter Condition Model
- `field: str` (required)
- `operator`: one of `equals | in | intersects | lt | lte | gt | gte | exists`
- `value: str | int | list[str] | list[int] | None`
- `source: "user"` (default `"user"`)

Minimum Validation/Test Contract
- A valid config MUST instantiate `ControlPlaneConfig` without error.
- Invalid cross-references (`default_policy`, `filter_name`, `apply_policy`) MUST fail with `ControlPlaneConfigValidationError`.
- Duplicate names (`policy`, `filter`, `org`, org-local `policy_rule`) MUST fail.
- Non-positive or duplicate org-local `policy_rule.priority` MUST fail.
- Rule condition source semantics SHOULD include unit coverage for nested user
  and document paths.

Reference Files
- Models:
  - `rag_control/models/config.py`
  - `rag_control/models/org.py`
  - `rag_control/models/policy.py`
  - `rag_control/models/rule.py`
  - `rag_control/models/filter.py`
- Loader:
  - `rag_control/core/config_loader.py`
