# Governance Contract

**Version:** v2026.1
**Status:** Draft
**Applies To:**
- `rag_control.governance.gov.GovernanceRegistry`
- `rag_control.models.deny_rule.DenyRule`
- `rag_control.models.deny_rule.DenyRuleCondition`
- `rag_control.models.deny_rule.DenyRuleLogicalCondition`

## Purpose

- Define the schema and evaluation semantics for request-time governance and access control.
- Enable organizations to enforce deny-rules based on user context and document properties.
- Provide clear guidance on deny-rule resolution order, condition matching, and document filtering.

## Normative Terms

- **MUST**: required.
- **SHOULD**: recommended unless system constraints prevent it.
- **MAY**: optional.

## Governance Registry: `GovernanceRegistry`

### Role
- Central component for evaluating deny-rules and policy resolution at request time.
- Loads and sorts rules by priority (descending) during initialization.
- Evaluates deny-rules before policy selection to enforce access control.

### Key Methods

#### `resolve_deny(user_context, source_documents, audit_context)`
- **Purpose**: Determine if a request should be denied based on deny-rules.
- **Inputs**:
  - `user_context: UserContext` (required) - user attributes and metadata
  - `source_documents: list[VectorStoreRecord] | None` (optional) - retrieved documents
  - `audit_context: AuditLoggingContext | None` (optional) - logging context
- **Behavior**:
  - Iterate through deny-rules in priority order (highest to lowest).
  - If any deny-rule's conditions match, raise `GovernancePolicyDeniedError`.
  - If no deny-rule matches, return normally (request allowed to proceed).
  - If `audit_context` is provided, log all denial events with rule name and details.
- **Errors**:
  - MUST raise `GovernancePolicyDeniedError` when a deny-rule matches.

#### `resolve_policy(user_context, audit_context)`
- **Purpose**: Select the appropriate policy for the request.
- **Inputs**:
  - `user_context: UserContext` (required)
  - `audit_context: AuditLoggingContext | None` (optional)
- **Behavior**:
  - Iterate through policy-rules in priority order (highest to lowest).
  - If a rule's conditions match:
    - If `effect: deny`, raise `GovernancePolicyDeniedError`.
    - If `effect: allow` and `apply_policy` is set, return that policy name.
    - If `effect: allow` without `apply_policy`, return the organization's `default_policy`.
  - If no rule matches, return the organization's `default_policy`.
- **Returns**: `str` - the resolved policy name.

## Deny Rule Model: `DenyRule`

### Fields
- `name: str` (required) - unique within the organization
- `description: str | None` (optional) - human-readable explanation
- `priority: int` (required)
  - MUST be `> 0`.
  - MUST be unique within the organization.
  - Higher values execute first (descending order).
- `when: DenyRuleLogicalCondition` (required) - logical condition for the rule

### Ordering and Evaluation
- Deny-rules MUST be sorted by priority (descending) during `GovernanceRegistry` initialization.
- Evaluation MUST use the sorted order, stopping at the first matching rule.
- Within a single rule, logical conditions are evaluated as specified in `DenyRuleLogicalCondition`.

## Deny Rule Condition Models

### `DenyRuleLogicalCondition`
- **Fields**:
  - `all: list[DenyRuleCondition] | None` (optional)
  - `any: list[DenyRuleCondition] | None` (optional)
- **Evaluation Semantics**:
  - If only `all` is present, all listed conditions MUST match.
  - If only `any` is present, at least one listed condition MUST match.
  - If both `all` and `any` are present, both groups MUST match (AND logic).
  - Empty lists SHOULD evaluate as non-match.

### `DenyRuleCondition`
- **Fields**:
  - `field: str` (required) - the field to evaluate (supports nested paths with dot notation)
  - `operator: str` (required) - one of `equals | lt | lte | gt | gte | intersects | exists`
  - `value: str | int | list[str] | list[int] | None` (optional, required for operators other than `exists`)
  - `source: str` (required) - one of `"user" | "documents"`
  - `document_match: "any" | "all" | None` (optional)
    - MUST be present if `source: "documents"`.
    - `"any"` - rule matches if at least one document satisfies the condition.
    - `"all"` - rule matches if every document satisfies the condition.
    - MUST NOT be present if `source: "user"`.

### Field Resolution

#### User Context Fields (`source: "user"`)
- Implementations MUST resolve:
  - Top-level `UserContext` fields (e.g., `user_id`, `org_id`)
  - Extra custom top-level fields on `UserContext`
  - Keys under `attributes` both with and without the `"attributes."` prefix
    - `department` resolves the same as `attributes.department`
  - Nested dot paths (e.g., `attributes.department`, `region.status.top`)
- Missing fields SHOULD evaluate as non-match.

#### Document Fields (`source: "documents"`)
- Implementations MUST resolve nested dot paths against `VectorStoreRecord` fields.
- Common document fields:
  - `metadata.source` - origin of the document
  - `metadata.classification` - data classification (e.g., restricted, confidential)
  - `metadata.data_classification` - data type classification (e.g., pii, phi)
  - `score` - retrieval confidence score
  - `metadata.days_old` - document age in days
- Missing fields in a document SHOULD evaluate as non-match for that document.

## Operators

### Common Operators (User and Document)
- **`equals`**: exact match
  - `"restriction" equals "restricted"` → `true` if the field value is exactly `"restricted"`
- **`lt` / `lte` / `gt` / `gte`**: numeric comparisons
  - `score lte 0.4` → `true` if score ≤ 0.4
  - `metadata.days_old gt 365` → `true` if document is older than 365 days
  - Operands MUST be numeric; non-numeric values MUST evaluate as non-match.
- **`intersects`**: membership or substring match
  - For lists/sets: `["pii", "phi"] intersects ["pii", "phi", "financial_records"]` → `true` if any value matches
  - For strings: `"restricted" intersects ["restricted", "confidential", "internal"]` → `true` if substring found
  - Non-list/non-string operands MUST evaluate as non-match.
- **`exists`**: field presence
  - No value required
  - `metadata.approval_status exists` → `true` if the field is present (non-null)

## Example Deny Rules

### Simple Single-Source Rules

**Example 1: Block untrusted document sources**
```yaml
- name: deny_untrusted_document_source
  description: Deny if any retrieved document comes from an untrusted source.
  priority: 60
  when:
    any:
      - field: metadata.source
        operator: equals
        value: public-web
        source: documents
        document_match: any
```

**Example 2: Block low-confidence documents**
```yaml
- name: deny_low_confidence_docs
  description: Deny responses when all retrieval documents have low confidence.
  priority: 10
  when:
    all:
      - field: score
        operator: lte
        value: 0.4
        source: documents
        document_match: all
```

### Complex Multi-Condition Rules

**Example 3: Block untrusted sources with low confidence**
```yaml
- name: deny_untrusted_and_low_confidence
  description: Deny if any doc is from untrusted source with low confidence score.
  priority: 55
  when:
    any:
      - and:
          - condition:
              field: metadata.source
              operator: in
              value:
                - public-web
                - external-forum
              source: documents
          - condition:
              field: score
              operator: lt
              value: 0.5
              source: documents
        document_match: any
```

**Example 4: Block multiple sensitive classifications**
```yaml
- name: deny_restricted_classification
  description: Deny when docs contain restricted or confidential classification.
  priority: 50
  when:
    any:
      - field: metadata.classification
        operator: intersects
        value:
          - restricted
          - confidential
          - internal-only
        source: documents
        document_match: any
```

### Mixed User and Document Rules

**Example 5: Restrict external users from accessing restricted documents**
```yaml
- name: deny_external_users_restricted_docs
  description: Deny external users from accessing restricted documents.
  priority: 48
  when:
    all:
      - field: user_type
        operator: equals
        value: external
        source: user
      - field: metadata.classification
        operator: equals
        value: restricted
        source: documents
        document_match: any
```

**Example 6: Block junior analysts from sensitive data**
```yaml
- name: deny_junior_analysts_sensitive_docs
  description: Deny junior analysts from accessing PII or confidential documents.
  priority: 35
  when:
    all:
      - field: attributes.clearance_level
        operator: lt
        value: 3
        source: user
      - field: metadata.data_classification
        operator: intersects
        value:
          - pii
          - confidential
        source: documents
        document_match: any
```

## Configuration at OrgConfig Level

### Organization Structure
```yaml
orgs:
  - org_id: acme_corp
    description: Organization name
    default_policy: policy_name
    policy_rules:
      # PolicyRules use user-context only (source: "user")
      - name: rule_name
        effect: allow
        apply_policy: policy_name
        priority: 50
        when: { ... }
    deny_rules:
      # DenyRules can use both user and document sources
      - name: rule_name
        priority: 60
        when: { ... }
```

### Initialization and Sorting
- During `GovernanceRegistry` initialization, each organization's deny-rules MUST be sorted by priority in descending order.
- Policy-rules MUST also be sorted by priority in descending order.
- This ensures consistent, predictable evaluation order at request time.

## Validation Invariants

### At Configuration Load Time
- All `policy_rules` and `deny_rules` within an organization MUST have unique names.
- All `policy_rules` and `deny_rules` within an organization MUST have unique priorities.
- All priorities MUST be `> 0`.
- If a deny-rule uses `source: "documents"`, it MUST specify `document_match: "any" | "all"`.
- If a deny-rule uses `source: "user"`, it MUST NOT specify `document_match`.

### At Request Time
- `resolve_deny()` MUST have access to `source_documents` if any deny-rule references `source: "documents"`.
  - If `source_documents` is `None` and a rule requires documents, that rule's document conditions SHOULD evaluate as non-match.
- Field resolution errors MUST NOT raise exceptions; missing fields MUST evaluate as non-match.

## Error Handling

### `GovernancePolicyDeniedError`
- Raised when a deny-rule's conditions match.
- **Fields**:
  - `user_context: UserContext` - the user who was denied
  - `rule_name: str` - the name of the deny-rule that triggered the denial
- Implementations SHOULD include the rule name in error messages for debugging.

### Audit Logging
- If `audit_context` is provided, implementations MUST log:
  - Event type: `"request.denied"`
  - Log level: `"warning"`
  - Rule name that triggered the denial
  - Error type and message

## Reference Files
- `rag_control/governance/gov.py` - GovernanceRegistry implementation
- `rag_control/models/deny_rule.py` - DenyRule and condition models
- `examples/policy_config.yaml` - example configurations with deny-rules
- Tests:
  - `tests/unit/test_governance_registry.py` - comprehensive unit tests
  - `tests/unit/test_config_validation_edges.py` - validation tests
