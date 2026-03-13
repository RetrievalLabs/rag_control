---
title: Governance
description: Comprehensive guide to governance and policy enforcement in rag_control
---

# Governance

Governance in rag_control provides organization-level control over policy enforcement, access, and security. It determines which policies apply to which requests, enables organization-specific overrides, and enforces organizational rules across your RAG application.

## What is Governance?

Governance is the set of rules that apply at the organization level. It answers critical questions:

- **Which policies apply?** - Different users/contexts may need different policies
- **When should requests be denied?** - What conditions warrant rejecting a request entirely
- **How do we prioritize rules?** - When multiple rules could apply, which takes precedence
- **What data is sensitive?** - How to handle different classification levels
- **Who can access what?** - Role-based and tier-based access control

The governance system bridges user context, documents, and policies to make intelligent, rule-based decisions about request handling.

## Core Concepts

### Organizations

Organizations are the fundamental unit of governance. Each organization has:

- A unique identifier
- A default policy (used when no rules match)
- Document retrieval settings
- Deny rules that enforce access control (evaluated first)
- Policy rules that determine which policy to apply (evaluated after deny rules)

```yaml
orgs:
  - org_id: acme_corp
    description: Acme Corporation - Enterprise Customer
    default_policy: standard
    deny_rules:
      # Access control rules (evaluated first)
    policy_rules:
      # Policy selection rules (evaluated after deny rules)
```

### Deny Rules vs Policy Rules

rag_control has two types of governance rules, evaluated in sequence:

| Aspect | Deny Rules | Policy Rules |
|--------|-----------|--------------|
| **Purpose** | Access control / blocking | Policy selection |
| **Execution** | Evaluated FIRST, before policy lookup | Evaluated AFTER deny rules |
| **Conditions** | User context + document properties | User context only |
| **Effect** | Block request immediately | Select policy to apply |
| **Use Case** | Enforce restrictions | Choose enforcement level |
| **Sources** | Mixed (user AND documents) | User only |

### Deny Rules

Deny rules provide fine-grained access control by blocking requests based on combined user and document context. They execute before policy rules and stop processing immediately when matched.

```yaml
deny_rules:
  - name: deny_untrusted_sources
    description: Block documents from untrusted sources
    priority: 100                    # Higher = evaluated first
    when:
      all:                           # All conditions must match (AND)
        - field: metadata.source
          operator: equals
          value: public-web
          source: documents
          document_match: any        # any or all (documents only)

  - name: deny_external_users_sensitive_docs
    description: Block external users from accessing sensitive data
    priority: 95
    when:
      all:
        - field: user_type
          operator: equals
          value: external
          source: user
        - field: metadata.classification
          operator: in
          value: [sensitive, confidential]
          source: documents
          document_match: any
```

**Key characteristics:**
- Can mix user context and document metadata in a single rule
- Support nested AND/OR logic with `all` and `any`
- `document_match: any` denies if any document matches the condition
- `document_match: all` denies only if all documents match the condition
- When matched, raise `GovernanceDenyRuleError` and stop processing

### Policy Rules

Policy rules determine which policy to apply to a request. They evaluate conditions and determine the outcome:

- **enforce**: Apply a specific policy to the request
- **deny**: Block the request (rarely used; prefer deny_rules for access control)

Rules are evaluated in **priority order** (highest first), and the first rule that matches determines the outcome.

```yaml
policy_rules:
  - name: apply_strict_citations
    priority: 100
    effect: enforce
    when:
      all:
        - field: org_tier
          operator: equals
          value: enterprise
          source: user
    apply_policy: strict_citations
```

### Rule Conditions

Conditions in the `when` clause determine when a rule applies. For policy rules, they check:

- **User context** - Who is making the request (org_id, tier, role, custom fields)

For deny rules, conditions can check:

- **User context** - Who is making the request
- **Document metadata** - What documents were retrieved (classification, source, sensitivity)

Multiple conditions can be combined with `all` (AND) or `any` (OR) logic.

## Organizations Configuration

### Organization Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | string | Yes | Unique organization identifier (e.g., `acme_corp`, `startup_xyz`) |
| `description` | string | No | Human-readable description for documentation |
| `default_policy` | string | Yes | Policy used if no deny/policy rule matches |
| `deny_rules` | array | No | Access control rules evaluated first (can be empty) |
| `policy_rules` | array | Yes | Policy selection rules (can be empty) |

### Complete Organization Example

```yaml
orgs:
  - org_id: enterprise_acme
    description: Acme Corp Enterprise - Premium tier with strict compliance
    default_policy: standard

    # Access control rules (evaluated first)
    deny_rules:
      - name: deny_untrusted_sources
        description: Block untrusted data sources
        priority: 100
        when:
          all:
            - field: metadata.source
              operator: in
              value: [public-web, unverified]
              source: documents
              document_match: any

      - name: deny_external_users_pii
        description: Block external users from PII documents
        priority: 95
        when:
          all:
            - field: user_type
              operator: equals
              value: external
              source: user
            - field: metadata.classification
              operator: equals
              value: pii
              source: documents
              document_match: any

    # Policy selection rules (evaluated after deny rules)
    policy_rules:
      - name: enforce_strict_for_sensitive
        priority: 100
        effect: enforce
        when:
          any:
            - field: metadata.classification
              operator: in
              value: [sensitive, confidential]
              source: documents
              document_match: any
        apply_policy: strict_citations

      - name: enforce_exploratory_for_research
        priority: 50
        effect: enforce
        when:
          all:
            - field: org_tier
              operator: equals
              value: enterprise
              source: user
            - field: role
              operator: equals
              value: researcher
              source: user
        apply_policy: exploratory
```

## Policy Rules

Policy rules determine which policy applies to a request. They execute **after** deny rules.

### Rule Structure

Every policy rule has:

- **name**: Unique identifier for the rule
- **description**: Human-readable explanation (recommended for audit trails)
- **priority**: Execution order (higher = evaluated first)
- **effect**: `allow` (permit and optionally apply policy) or rarely `deny` (use deny_rules instead)
- **when**: Conditions that must match (user context only)
- **apply_policy**: (optional) Which policy to apply when rule matches

```yaml
- name: rule_name
  description: What this rule does and why
  priority: 75
  effect: allow
  when:
    all:
      - field: org_tier
        operator: equals
        value: enterprise
        source: user
  apply_policy: strict_citations
```

### Policy Rule Effects

#### Allow: Apply a Policy

When `effect: allow`, the rule permits the request and optionally applies a specific policy:

```yaml
- name: enforce_strict_for_enterprise
  description: Enterprise customers always use strict citation policy
  priority: 100
  effect: allow
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
  apply_policy: strict_citations
```

**Behavior:**
- Request proceeds with the specified policy (if `apply_policy` provided)
- Metrics record which policy was applied with `policy.resolved_by_name` counter
- If no `apply_policy`, organization's `default_policy` is used

### Deny Rules for Access Control

**Note:** For access control and blocking requests, use deny_rules instead of policy rules with `effect: deny`. Deny rules support mixed user and document conditions and execute earlier in the request flow.

See [Deny Rules](#deny-rules) section above for detailed access control patterns.

### Deny Rule Error Handling

When a deny rule matches, it raises an exception that can be caught:

```python
from rag_control.exceptions.governance import GovernancePolicyDeniedError
from rag_control.core.engine import RAGControl

try:
    result = engine.run(user_context=user_context, query=query)
except GovernancePolicyDeniedError as e:
    # Handle denial
    print(f"Request denied: {e}")
    print(f"Org: {e.user_context.org_id}")
    print(f"Rule: {e.rule_name}")
    # Return user-friendly error message
    return {"error": "Your request cannot be processed due to governance policy"}
```

### Rule Conditions

#### Condition Structure

For policy rules (user context only):

```yaml
when:
  all:                              # all or any
    - field: org_tier
      operator: equals
      value: enterprise
      source: user                  # user only for policy rules
```

For deny rules (user and/or documents):

```yaml
when:
  all:                              # all or any
    - field: user_clearance_level
      operator: gte
      value: 3
      source: user
    - field: metadata.classification
      operator: equals
      value: confidential
      source: documents
      document_match: any           # any or all (documents only)
```

#### Operators

| Operator | Supported Values | Description |
|----------|------------------|-------------|
| `equals` | Any | Exact match |
| `lt` | Number | Less than |
| `lte` | Number | Less than or equal to |
| `gt` | Number | Greater than |
| `gte` | Number | Greater than or equal to |
| `in` | List | Field value is in provided list |
| `intersects` | List | Field array intersects with provided list |
| `exists` | N/A | Field exists (no value needed) |

#### Sources

**User source** - Check fields from user context (policy rules and deny rules):

```yaml
- field: org_tier
  operator: equals
  value: enterprise
  source: user
```

Available user fields: `org_id`, `user_id`, `org_tier`, `role`, `environment`, and custom fields.

**Documents source** - Check metadata from retrieved documents (deny rules only):

```yaml
- field: metadata.classification
  operator: in
  value: [sensitive, confidential]
  source: documents
  document_match: any
```

Document matching (required when `source: documents` in deny rules):

- `any`: Deny if **any document** matches the condition (block on first match)
- `all`: Deny only if **all documents** match the condition (allow if any escapes)

Example: Deny if **any** document is confidential:

```yaml
- field: metadata.classification
  operator: equals
  value: confidential
  source: documents
  document_match: any          # Block if ANY doc is confidential
```

Example: Deny only if **all** documents are experimental:

```yaml
- field: metadata.status
  operator: equals
  value: experimental
  source: documents
  document_match: all          # Only block if ALL docs are experimental
```

## Practical Examples

### Example 1: Enterprise Customer with Tiered Policies

An enterprise customer needs different policies based on user role, with access control for untrusted sources:

```yaml
- org_id: enterprise_acme
  description: Acme Corp - Enterprise with role-based policies
  default_policy: standard

  # Block untrusted sources for all users
  deny_rules:
    - name: deny_untrusted_sources
      priority: 100
      when:
        all:
          - field: metadata.source
            operator: in
            value: [public-web, unverified]
            source: documents
            document_match: any

  # Select policy based on role
  policy_rules:
    # Analysts get exploratory access
    - name: analysts_use_exploratory
      priority: 100
      effect: allow
      when:
        all:
          - field: role
            operator: equals
            value: analyst
            source: user
          - field: org_id
            operator: equals
            value: enterprise_acme
            source: user
      apply_policy: exploratory

    # Executives see only strict citations
    - name: executives_strict_only
      priority: 95
      effect: allow
      when:
        all:
          - field: role
            operator: in
            value: [director, executive, ceo]
            source: user
          - field: org_id
            operator: equals
            value: enterprise_acme
            source: user
      apply_policy: strict_citations

    # Everyone else gets standard policy
    - name: default_to_standard
      priority: 10
      effect: allow
      when:
        all:
          - field: org_id
            operator: equals
            value: enterprise_acme
            source: user
      apply_policy: standard
```

### Example 2: Compliance and Data Classification

Handle requests based on document sensitivity with access control and policy selection:

```yaml
orgs:
  - org_id: compliance_org
    default_policy: standard

    # Access control - deny certain combinations
    deny_rules:
      # Block PII access entirely
      - name: block_pii_access
        priority: 100
        when:
          all:
            - field: metadata.classification
              operator: equals
              value: pii
              source: documents
              document_match: any

      # Block external users from confidential documents
      - name: deny_external_users_confidential
        priority: 95
        when:
          all:
            - field: user_type
              operator: equals
              value: external
              source: user
            - field: metadata.classification
              operator: equals
              value: confidential
              source: documents
              document_match: any

    # Policy selection based on document sensitivity
    policy_rules:
      # Confidential documents require strict citations
      - name: strict_for_confidential
        priority: 90
        effect: allow
        when:
          any:
            - field: metadata.classification
              operator: equals
              value: confidential
              source: documents
              document_match: any
        apply_policy: strict_citations

      # Internal documents allow exploratory access
      - name: exploratory_for_internal
        priority: 50
        effect: allow
        when:
          all:
            - field: metadata.classification
              operator: equals
              value: internal
              source: documents
              document_match: all
        apply_policy: exploratory
```

### Example 3: Environment-Based Policies

Different rules for development vs. production, with stricter access control in production:

```yaml
orgs:
  - org_id: multi_env
    default_policy: standard

    # Production-only access control
    deny_rules:
      # In production: deny unverified sources
      - name: deny_unverified_production
        priority: 100
        when:
          all:
            - field: environment
              operator: equals
              value: production
              source: user
            - field: metadata.is_verified
              operator: equals
              value: false
              source: documents
              document_match: any

    # Environment-based policy selection
    policy_rules:
      # Production: strict and safe
      - name: production_strict
        priority: 100
        effect: allow
        when:
          all:
            - field: environment
              operator: equals
              value: production
              source: user
        apply_policy: strict_citations

      # Development: allow exploratory access
      - name: development_exploratory
        priority: 90
        effect: allow
        when:
          all:
            - field: environment
              operator: equals
              value: development
              source: user
        apply_policy: exploratory

      # Staging: standard policy by default
      - name: staging_standard
        priority: 80
        effect: allow
        when:
          all:
            - field: environment
              operator: equals
              value: staging
              source: user
        apply_policy: standard
```

### Example 4: Multiple Organizations with Different Access Control

Different access control and policies for different customer tiers:

```yaml
orgs:
  - org_id: free_tier_startup
    default_policy: exploratory

    # Free tier: strict access control
    deny_rules:
      # Free tier: deny access to premium data
      - name: free_tier_no_premium
        priority: 100
        when:
          all:
            - field: metadata.tier
              operator: equals
              value: premium
              source: documents
              document_match: any

    policy_rules: []

  - org_id: professional_tier
    default_policy: standard

    # Professional tier: moderate access control
    deny_rules:
      # Professional tier: deny clearly unvetted sources
      - name: professional_unvetted_only
        priority: 100
        when:
          any:
            - field: metadata.source
              operator: in
              value: [unvetted-web, suspicious]
              source: documents
              document_match: any

    policy_rules: []

  - org_id: enterprise_tier
    default_policy: strict_citations

    # Enterprise: permissive access control, policy-driven
    deny_rules:
      # Enterprise: only deny PII
      - name: enterprise_block_pii
        priority: 100
        when:
          all:
            - field: metadata.classification
              operator: equals
              value: pii
              source: documents
              document_match: any

    policy_rules:
      # Enterprise users can request specific policies
      - name: enforce_strict_when_requested
        priority: 50
        effect: allow
        when:
          all:
            - field: request_strict_policy
              operator: equals
              value: true
              source: user
        apply_policy: strict_citations
```

### Example 5: Complex Multi-Condition Rules

Combining multiple conditions with AND/OR logic in deny and policy rules:

```yaml
orgs:
  - org_id: complex_rules_org
    default_policy: standard

    # Complex deny rules with mixed conditions
    deny_rules:
      # Deny if BOTH sensitive docs AND external user
      - name: deny_sensitive_external_user
        priority: 100
        when:
          all:
            # Must be external user
            - field: user_type
              operator: equals
              value: external
              source: user
            # AND must have sensitive docs
            - field: metadata.classification
              operator: in
              value: [sensitive, confidential]
              source: documents
              document_match: any

      # Deny if ANY of these risky conditions
      - name: deny_risky_documents
        priority: 95
        when:
          any:
            # Unverified sources
            - field: metadata.is_verified
              operator: equals
              value: false
              source: documents
              document_match: any
            # Very old documents
            - field: metadata.age_days
              operator: gt
              value: 1095
              source: documents
              document_match: any
            # Deprecated content
            - field: metadata.is_deprecated
              operator: equals
              value: true
              source: documents
              document_match: any

    # Complex policy rules
    policy_rules:
      # Enforce strict policy if ANY risk indicator present
      - name: enforce_strict_if_risk
        priority: 80
        effect: allow
        when:
          any:
            # Sensitive classification
            - field: metadata.classification
              operator: equals
              value: confidential
              source: documents
              document_match: any
            # Recent/active content (needs strict handling)
            - field: metadata.is_active
              operator: equals
              value: true
              source: documents
              document_match: all
        apply_policy: strict_citations

      # Use exploratory only for safe, verified content
      - name: exploratory_for_verified_internal
        priority: 70
        effect: allow
        when:
          all:
            - field: metadata.is_verified
              operator: equals
              value: true
              source: documents
              document_match: all
            - field: metadata.classification
              operator: equals
              value: internal
              source: documents
              document_match: all
        apply_policy: exploratory
```

## Rule Priority and Evaluation

Rules are evaluated in **priority order** (highest number first), and the first matching rule determines the outcome.

```yaml
policy_rules:
  # Priority 100: Evaluated first (critical rules)
  - name: critical_deny_rule
    priority: 100
    effect: deny

  # Priority 50: Evaluated second
  - name: standard_enforcement
    priority: 50
    effect: enforce

  # Priority 10: Evaluated last (fallback)
  - name: fallback_enforcement
    priority: 10
    effect: enforce
```

### Priority Best Practices

- **100+**: Critical security rules (denials, PII handling)
- **50-99**: Standard business rules
- **10-49**: Fallback/default rules

**Example priority scheme:**

```yaml
policy_rules:
  - name: deny_pii
    priority: 100          # Always evaluate first

  - name: deny_untrusted_sources
    priority: 95

  - name: enforce_strict_for_sensitive
    priority: 80

  - name: enforce_exploratory_for_research
    priority: 50

  - name: enforce_standard_default
    priority: 10           # Only if nothing above matches
```

## User Context

User context is passed with each request and contains information about who is making the request:

```python
from rag_control.models.user import UserContext

user_context = UserContext(
    org_id="enterprise_acme",      # Required: which organization
    user_id="user-12345",          # Required: who is making request
    org_tier="enterprise",         # Optional: organization tier (free, standard, enterprise)
    role="analyst",                # Optional: user's role
    environment="production",      # Optional: execution environment
    # Custom fields are supported
    department="research",
    clearance_level="secret",
)
```

### Standard Fields

| Field | Type | Example | Used For |
|-------|------|---------|----------|
| `org_id` | string | `enterprise_acme` | Identifying organization |
| `user_id` | string | `user-12345` | Audit trails |
| `org_tier` | string | `enterprise`, `standard`, `free` | Tier-based policies |
| `role` | string | `analyst`, `executive`, `researcher` | Role-based access |
| `environment` | string | `production`, `staging`, `development` | Environment-specific rules |

### Custom Fields

You can add any custom fields to user context for your governance rules:

```python
user_context = UserContext(
    org_id="acme_corp",
    user_id="user-123",
    # Custom fields
    compliance_mode=True,
    max_sensitivity_level="confidential",
    needs_audit_trail=True,
)
```

Then reference them in rules:

```yaml
policy_rules:
  - name: strict_when_compliance_mode
    priority: 100
    effect: enforce
    when:
      all:
        - field: compliance_mode
          operator: equals
          value: "true"
          source: user
    policy: strict_citations
```

## Execution Flow

When a request arrives, governance executes this flow:

```
1. Extract user_context from request
           ↓
2. Validate organization exists (user_context.org_id)
           ↓
3. Retrieve documents from vector store
           ↓
4. Evaluate deny_rules in priority order (highest first)
           ├─ For each deny rule:
           │  - Evaluate conditions (can use user context + document metadata)
           │  - If conditions match:
           │    └─ Block request, raise GovernancePolicyDeniedError
           ↓
5. If no deny rule matched, evaluate policy_rules in priority order
           ├─ For each policy rule:
           │  - Evaluate conditions (user context only)
           │  - If conditions match:
           │    ├─ effect: allow → Apply specified policy, continue
           │    └─ effect: deny → (rare) Block request
           ↓
6. If no policy rule matched:
   - Apply organization's default_policy
           ↓
7. Execute request with chosen policy
```

### Example Execution

Given this configuration:

```yaml
orgs:
  - org_id: acme_corp
    default_policy: standard

    deny_rules:
      - name: deny_untrusted_external
        priority: 100
        when:
          all:
            - field: user_type
              operator: equals
              value: external
              source: user
            - field: source
              operator: equals
              value: untrusted
              source: documents
              document_match: any

    policy_rules:
      - name: enforce_strict_sensitive
        priority: 50
        effect: allow
        when:
          all:
            - field: metadata.classification
              operator: equals
              value: confidential
              source: documents
              document_match: any
        apply_policy: strict_citations
```

And this request:

```python
UserContext(
    org_id="acme_corp",
    user_id="user-1",
    user_type="internal",
    role="analyst",
)
# Documents retrieved: [
#   {metadata: {classification: "confidential", source: "internal"}},
#   {metadata: {classification: "internal", source: "internal"}},
# ]
```

**Execution:**

1. ✓ Org exists: `acme_corp`
2. ✓ Retrieve documents from vector store
3. ✓ Evaluate deny rules (priority 100):
   - Check if `user_type == external` AND ANY document has `source == untrusted`
   - User is `internal`, documents are from `internal` source → No match
4. ✓ Evaluate policy rules (priority 50):
   - Check if ANY document has `classification == confidential`
   - First document has `classification: confidential` → Match!
   - Apply `strict_citations` policy
5. Request proceeds with `strict_citations` policy

## Error Handling and Denial Reporting

When a request is denied by governance, the system:

1. **Raises Exception**: `GovernancePolicyDeniedError` is raised immediately
2. **Records Metrics**: Increments `requests.denied` counter with error categorization
3. **Logs Audit Event**: Records denial in audit logs with rule name and details
4. **Stops Processing**: Request never proceeds to policy enforcement or document retrieval

### Exception Raised

When a deny rule matches, `GovernancePolicyDeniedError` is raised with:

- **user_context**: The UserContext that triggered the denial
- **rule_name**: Name of the deny rule that matched
- **Message**: `"governance policy denied for org 'org_id' by rule 'rule_name'"`

### Example Denial Scenario

Configuration:

```yaml
policy_rules:
  - name: block_external_in_production
    priority: 100
    effect: deny
    when:
      all:
        - field: environment
          operator: equals
          value: production
          source: user
        - field: source
          operator: equals
          value: external
          source: documents
          document_match: any
```

When denied:

```python
from rag_control.exceptions.governance import GovernancePolicyDeniedError

try:
    result = engine.run(user_context=user_context, query=query)
except GovernancePolicyDeniedError as e:
    # e.user_context.org_id: Organization that was denied
    # e.rule_name: "block_external_in_production"
    # str(e): "governance policy denied for org 'org_id' by rule 'block_external_in_production'"

    # Audit event logged:
    # {
    #   "event": "request.denied",
    #   "level": "warning",
    #   "rule_name": "block_external_in_production",
    #   "error_type": "GovernancePolicyDeniedError"
    # }

    # Metrics recorded:
    # - requests.denied counter incremented
    # - error_category: "governance"
    # - error_type: "GovernancePolicyDeniedError"
```

### Handling Denials in Your Application

Best practices for catching and responding to denials:

```python
from rag_control.exceptions.governance import GovernancePolicyDeniedError
from rag_control.core.engine import Engine

engine = Engine(config)

def process_query(user_context, query):
    try:
        result = engine.run(user_context=user_context, query=query)
        return {"success": True, "result": result}
    except GovernancePolicyDeniedError as e:
        # Log for audit purposes
        logger.warning(f"Request denied by rule: {e.rule_name}")

        # Return user-friendly error
        return {
            "success": False,
            "error": "Your request cannot be processed due to security policy",
            "rule": e.rule_name,  # Optionally include for debugging
        }
    except Exception as e:
        # Handle other errors differently
        logger.error(f"Processing error: {e}")
        return {"success": False, "error": "Processing failed"}
```

### Distinguish Denial Types

If you need to distinguish governance denials from other errors:

```python
from rag_control.exceptions.governance import GovernancePolicyDeniedError

try:
    result = engine.run(user_context=user_context, query=query)
except GovernancePolicyDeniedError as e:
    # Governance-level denial (organization rules blocked request)
    logger.warning(f"Governance denial by rule '{e.rule_name}' for org '{e.user_context.org_id}'")
    # Return 403 Forbidden or similar
    return error_response("Access denied by policy", status_code=403)
except Exception as e:
    # Other errors (embedding failures, retrieval errors, etc.)
    logger.error(f"Processing error: {e}")
    return error_response("Processing failed", status_code=500)
```

## Best Practices

### 1. Separate Deny Rules from Policy Rules

Use deny rules for access control and blocking, use policy rules for policy selection:

```yaml
orgs:
  - org_id: example
    default_policy: standard

    # Deny rules: Access control
    deny_rules:
      # Priority 100+: Critical blocks (PII, security)
      - name: block_pii
        priority: 110

      # Priority 80-99: Compliance blocks
      - name: deny_external_confidential
        priority: 95

    # Policy rules: Policy selection
    policy_rules:
      # Priority 100+: Critical enforcement
      - name: enforce_strict_for_sensitive
        priority: 100
        effect: allow

      # Priority 50-99: Standard business rules
      - name: enforce_exploratory_for_research
        priority: 60
        effect: allow

      # Priority 10-49: Defaults
      - name: apply_default_policy
        priority: 10
        effect: allow
```

### 2. Organize Rules by Priority Tiers

Within deny rules and policy rules, use consistent priority bands:

**Deny Rules:**
```yaml
deny_rules:
  # Tier 1: Critical Security (100+)
  - priority: 110      # Block PII
  - priority: 105      # Block secrets

  # Tier 2: Compliance (90-99)
  - priority: 95       # Restrict by role
  - priority: 90       # Verify sources

  # Tier 3: Business Rules (50-89)
  - priority: 70       # Custom restrictions
```

**Policy Rules:**
```yaml
policy_rules:
  # Tier 1: Critical Policies (100+)
  - priority: 100      # Force strict policy

  # Tier 2: Standard Rules (50-99)
  - priority: 75       # Role-based policies
  - priority: 60       # Tier-based policies

  # Tier 3: Defaults (10-49)
  - priority: 10       # Default enforcement
```

### 3. Use Descriptive Names and Descriptions

```yaml
deny_rules:
  - name: deny_pii_external_users    # Clear what it does
    description: |
      Block external users from accessing PII-containing documents.
      Required for GDPR compliance. See GDPR requirements in wiki.
    priority: 100

policy_rules:
  - name: enforce_strict_for_sensitive
    description: |
      Enforce strict citation policy for sensitive documents.
      Ensures all claims are properly sourced. See policies.md for details.
    priority: 100
    effect: allow
```

### 4. Test Conditions Against Real Data

Before deploying, verify conditions work with actual user contexts and documents:

```python
# Test deny rules
deny_test_cases = [
    {
        "name": "external_user_with_pii",
        "user_context": UserContext(org_id="example", user_type="external"),
        "documents": [{"metadata": {"classification": "pii"}}],
        "expected_rule": "deny_pii_external_users",
        "should_be_denied": True,
    },
]

# Test policy rules
policy_test_cases = [
    {
        "name": "analyst_with_confidential",
        "user_context": UserContext(org_id="example", role="analyst"),
        "documents": [{"metadata": {"classification": "confidential"}}],
        "expected_rule": "enforce_strict_for_sensitive",
        "expected_policy": "strict_citations",
    },
]
```

### 5. Document Rules for Audit Trails

Include rationale and references for both deny and policy rules:

```yaml
deny_rules:
  - name: block_regulated_data
    description: |
      Block access to regulated data (HIPAA, GDPR, SOC2).

      Applies to:
      - Customer health information (HIPAA)
      - EU resident personal data (GDPR)
      - SOC2-classified data

      See governance policy document v2.1
      Owner: compliance-team@company.com
    priority: 110

policy_rules:
  - name: enforce_strict_for_regulated_data
    description: |
      Enforce strict policy for regulated data when access is permitted.

      Ensures strong citation validation and external knowledge prevention.
      See governance policy document v2.1
      Owner: compliance-team@company.com
    priority: 100
    effect: allow
    apply_policy: strict_citations
```

### 6. Use Document Matching Strategically

In deny rules, choose matching mode based on security posture:

- `document_match: any` → Deny if **any** document matches (conservative, safer)
- `document_match: all` → Deny only if **all** documents match (permissive, less safe)

```yaml
deny_rules:
  # Conservative: deny if ANY untrusted source
  - name: deny_any_untrusted
    priority: 100
    when:
      - field: metadata.source
        operator: equals
        value: untrusted
        source: documents
        document_match: any   # Safer: blocks on first match

  # Permissive: deny only if ALL documents are experimental
  - name: deny_all_experimental
    priority: 90
    when:
      - field: metadata.status
        operator: equals
        value: experimental
        source: documents
        document_match: all   # Less safe: requires all to match

policy_rules:
  # Use any for stricter policy enforcement
  - name: enforce_strict_if_any_sensitive
    priority: 100
    effect: allow
    when:
      - field: metadata.classification
        operator: equals
        value: confidential
        source: documents
        document_match: any
    apply_policy: strict_citations
```

### 7. Avoid Overlapping Rules

If possible, make rule conditions mutually exclusive:

```yaml
# Instead of overlapping rules:
deny_rules:
  - name: deny_rule_a
    priority: 100
    when:
      - field: user_type
        operator: equals
        value: external
        source: user

  - name: deny_rule_b
    priority: 90
    when:
      - field: user_type
        operator: equals
        value: external  # Same condition!

# Use clear non-overlapping conditions:
deny_rules:
  - name: deny_external_with_pii
    priority: 100
    when:
      all:
        - field: user_type
          operator: equals
          value: external
          source: user
        - field: metadata.classification
          operator: equals
          value: pii
          source: documents
          document_match: any

  - name: deny_external_with_confidential
    priority: 90
    when:
      all:
        - field: user_type
          operator: equals
          value: external
          source: user
        - field: metadata.classification
          operator: equals
          value: confidential
          source: documents
          document_match: any
```

## Integration with Policies

Governance and policies work together:

- **Governance** answers: *Which policy should apply?*
- **Policies** answer: *What constraints should be enforced?*

Example flow:

```
Request arrives
     ↓
Governance selects policy (via rules)
     ↓
Policy enforces constraints (citations, length, etc.)
     ↓
Response generated with policy applied
```

See [Policies](/concepts/policies) for detailed policy configuration.

## Common Patterns

### Pattern: Tier-Based Access

Different policies for different customer tiers with access control:

```yaml
orgs:
  - org_id: multi_tier
    default_policy: exploratory

    deny_rules:
      # Free tier: block premium data
      - name: free_tier_no_premium
        priority: 100
        when:
          all:
            - field: org_tier
              operator: equals
              value: free
              source: user
            - field: metadata.tier
              operator: equals
              value: premium
              source: documents
              document_match: any

    policy_rules:
      - name: free_tier_exploratory
        priority: 100
        effect: allow
        when:
          - field: org_tier
            operator: equals
            value: free
            source: user
        apply_policy: exploratory

      - name: standard_tier_standard
        priority: 90
        effect: allow
        when:
          - field: org_tier
            operator: equals
            value: standard
            source: user
        apply_policy: standard

      - name: enterprise_tier_strict
        priority: 80
        effect: allow
        when:
          - field: org_tier
            operator: equals
            value: enterprise
            source: user
        apply_policy: strict_citations
```

### Pattern: Role-Based Access

Different access for different roles:

```yaml
orgs:
  - org_id: role_based
    default_policy: standard

    deny_rules:
      # Only contractors cannot access confidential
      - name: deny_contractors_confidential
        priority: 100
        when:
          all:
            - field: role
              operator: equals
              value: contractor
              source: user
            - field: metadata.classification
              operator: equals
              value: confidential
              source: documents
              document_match: any

    policy_rules:
      - name: analyst_exploratory
        priority: 100
        effect: allow
        when:
          - field: role
            operator: in
            value: [analyst, data_scientist, researcher]
            source: user
        apply_policy: exploratory

      - name: manager_standard
        priority: 90
        effect: allow
        when:
          - field: role
            operator: equals
            value: manager
            source: user
        apply_policy: standard

      - name: executive_strict
        priority: 80
        effect: allow
        when:
          - field: role
            operator: equals
            value: executive
            source: user
        apply_policy: strict_citations
```

### Pattern: Data Sensitivity

Rules based on document classification with multi-level access control:

```yaml
orgs:
  - org_id: sensitivity_based
    default_policy: exploratory

    deny_rules:
      # Block all access to PII
      - name: deny_all_pii
        priority: 100
        when:
          - field: metadata.classification
            operator: equals
            value: pii
            source: documents
            document_match: any

      # Block external users from confidential
      - name: deny_external_confidential
        priority: 95
        when:
          all:
            - field: user_type
              operator: equals
              value: external
              source: user
            - field: metadata.classification
              operator: equals
              value: confidential
              source: documents
              document_match: any

    policy_rules:
      - name: strict_for_confidential
        priority: 90
        effect: allow
        when:
          - field: metadata.classification
            operator: equals
            value: confidential
            source: documents
            document_match: any
        apply_policy: strict_citations

      - name: standard_for_internal
        priority: 80
        effect: allow
        when:
          - field: metadata.classification
            operator: equals
            value: internal
            source: documents
            document_match: all
        apply_policy: standard
```

## Troubleshooting

### Rule Not Matching

Debug rule matching:

1. **Check organization exists**: Is `user_context.org_id` in your config?
2. **Verify condition fields**: Does the user context or documents have the fields you're checking?
3. **Test operators**: Use correct operator (`equals` vs `in`, `contains`, etc.)
4. **Check document_match**: For document conditions, is `any` or `all` appropriate?

### Unexpected Policy Applied

If the wrong policy is applied:

1. **Check priority order**: Higher priority rules evaluated first
2. **Verify conditions**: Are all conditions in `when` clause matching?
3. **Test with real data**: Print actual user context and documents being checked
4. **Add logging**: Check execution flow to see which rule matched

## See Also

- [Policies Documentation](/concepts/policies) - Policy constraints and enforcement
- [Core Concepts Overview](/concepts/overview) - How everything fits together
- [Configuration Guide](/getting-started/configuration) - Setting up governance
- [API Reference](/api/models) - Detailed user context and model reference
