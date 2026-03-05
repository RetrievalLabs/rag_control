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
- Policy rules that determine which policy to apply

```yaml
orgs:
  - org_id: acme_corp
    description: Acme Corporation - Enterprise Customer
    default_policy: standard
    document_policy:
      top_k: 10
      filters: [internal_only]
    policy_rules:
      # Rules specific to this organization
```

### Policy Rules

Policy rules are the decision engine of governance. They evaluate conditions and determine the outcome:

- **enforce**: Apply a specific policy to the request
- **deny**: Block the request entirely

Rules are evaluated in **priority order** (highest first), and the first rule that matches determines the outcome.

```yaml
policy_rules:
  - name: block_external_data_in_compliance_mode
    priority: 100
    effect: deny
    when:
      all:
        - field: compliance_mode
          operator: equals
          value: "true"
          source: user
        - field: source
          operator: in
          value: [public-web, external]
          source: documents
          document_match: any
```

### Rule Conditions

Conditions in the `when` clause determine when a rule applies. They can check:

- **User context** - Who is making the request (org_id, tier, role, custom fields)
- **Document metadata** - What documents were retrieved (classification, source, sensitivity)

Multiple conditions can be combined with `all` (AND) or `any` (OR) logic.

## Organizations Configuration

### Organization Fields

| Field | Type | Description |
|-------|------|-------------|
| `org_id` | string | Unique organization identifier (e.g., `acme_corp`, `startup_xyz`) |
| `description` | string | Human-readable description for documentation |
| `default_policy` | string | Policy used if no rule matches |
| `document_policy` | object | Document retrieval settings (top_k, filters) |
| `policy_rules` | array | Rules that determine policy enforcement |

### Complete Organization Example

```yaml
orgs:
  - org_id: enterprise_acme
    description: Acme Corp Enterprise - Premium tier with strict compliance
    default_policy: standard
    document_policy:
      top_k: 10
      filters: [internal_only, approved_sources]
    policy_rules:
      - name: enforce_strict_for_sensitive
        priority: 100
        effect: enforce
        when:
          any:
            - field: metadata.classification
              operator: in
              value: [sensitive, confidential, pii]
              source: documents
              document_match: any
        policy: strict_citations

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
        policy: exploratory

      - name: deny_public_sources_in_production
        priority: 80
        effect: deny
        when:
          all:
            - field: environment
              operator: equals
              value: production
              source: user
            - field: source
              operator: in
              value: [public-web]
              source: documents
              document_match: any
```

## Policy Rules

### Rule Structure

Every rule has:

- **name**: Unique identifier for the rule
- **description**: Human-readable explanation (recommended for audit trails)
- **priority**: Execution order (higher = evaluated first)
- **effect**: Either `enforce` (apply policy) or `deny` (block request)
- **when**: Conditions that must match
- **policy**: (enforce only) Which policy to apply

```yaml
- name: rule_name
  description: What this rule does and why
  priority: 75
  effect: enforce
  when:
    all:
      - field: org_tier
        operator: equals
        value: enterprise
        source: user
  policy: strict_citations
```

### Rule Effects

#### Enforce: Apply a Policy

When `effect: enforce`, the rule applies a specific policy to the request:

```yaml
- name: enforce_strict_for_enterprise
  description: Enterprise customers always use strict citation policy
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

**Behavior:**
- Request proceeds with the specified policy
- Metrics record which policy was applied
- Metrics include a `policy.resolved_by_name` counter

#### Deny: Block the Request

When `effect: deny`, the request is rejected entirely:

```yaml
- name: deny_untrusted_sources_in_production
  description: Block requests that use untrusted/unvetted data sources
  priority: 90
  effect: deny
  when:
    all:
      - field: environment
        operator: equals
        value: production
        source: user
      - field: source
        operator: equals
        value: untrusted
        source: documents
        document_match: any
```

**Behavior:**
- Request is blocked and `GovernancePolicyDeniedError` exception is raised
- No policy is applied
- Metrics record the denial with appropriate error categorization
- Error category is `governance` or `enforcement` depending on context

**Exception Details:**

```python
from rag_control.exceptions.governance import GovernancePolicyDeniedError

# Exception is raised with:
# - user_context: The UserContext that triggered the denial
# - rule_name: Name of the deny rule that matched
# - Message: "governance policy denied for org 'org_id' by rule 'rule_name'"
```

**Catching and Handling Denials:**

```python
from rag_control.exceptions.governance import GovernancePolicyDeniedError
from rag_control.core.engine import Engine

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

```yaml
when:
  all:                              # all or any
    - field: user.role
      operator: equals
      value: analyst
      source: user                  # user or documents
      document_match: any           # any or all (documents only)
```

#### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Exact match | `value: "enterprise"` |
| `not_equals` | Not equal | `value: "free"` |
| `contains` | String contains | `value: "sensitive"` |
| `not_contains` | Does not contain | `value: "deprecated"` |
| `in` | Value in list | `value: [admin, manager]` |
| `not_in` | Value not in list | `value: [restricted, archived]` |

#### Sources

**User source** - Check fields from user context:

```yaml
- field: org_tier
  operator: equals
  value: enterprise
  source: user
```

Available user fields: `org_id`, `user_id`, `org_tier`, `role`, and custom fields.

**Documents source** - Check metadata from retrieved documents:

```yaml
- field: metadata.classification
  operator: in
  value: [sensitive, confidential]
  source: documents
  document_match: any
```

Document matching (required when `source: documents`):

- `any`: Rule matches if **any document** matches the condition
- `all`: Rule matches only if **all documents** match the condition

Example: Deny if **any** untrusted source is in results:

```yaml
- field: source
  operator: equals
  value: untrusted
  source: documents
  document_match: any          # Match if ANY doc is untrusted
```

Example: Apply strict policy only if **all** documents are sensitive:

```yaml
- field: metadata.classification
  operator: equals
  value: confidential
  source: documents
  document_match: all          # Match only if ALL docs are confidential
```

## Practical Examples

### Example 1: Enterprise Customer with Tiered Policies

An enterprise customer needs different policies based on user role:

```yaml
- org_id: enterprise_acme
  description: Acme Corp - Enterprise with role-based policies
  default_policy: standard
  document_policy:
    top_k: 20
    filters: [verified_sources]
  policy_rules:
    # Analysts get exploratory access
    - name: analysts_use_exploratory
      priority: 100
      effect: enforce
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
      policy: exploratory

    # Executives see only strict citations
    - name: executives_strict_only
      priority: 95
      effect: enforce
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
      policy: strict_citations

    # Everyone else gets standard policy
    - name: default_to_standard
      priority: 10
      effect: enforce
      when:
        all:
          - field: org_id
            operator: equals
            value: enterprise_acme
            source: user
      policy: standard
```

### Example 2: Compliance and Data Classification

Handle requests based on document sensitivity:

```yaml
policy_rules:
  # PII and secrets require strictest policy
  - name: block_pii_handling
    priority: 100
    effect: deny
    when:
      any:
        - field: metadata.classification
          operator: equals
          value: pii
          source: documents
          document_match: any
        - field: metadata.contains_secrets
          operator: equals
          value: "true"
          source: documents
          document_match: any

  # Confidential documents require strict citations
  - name: strict_for_confidential
    priority: 90
    effect: enforce
    when:
      any:
        - field: metadata.classification
          operator: equals
          value: confidential
          source: documents
          document_match: any
    policy: strict_citations

  # Internal documents allow exploratory access
  - name: exploratory_for_internal
    priority: 50
    effect: enforce
    when:
      all:
        - field: metadata.classification
          operator: equals
          value: internal
          source: documents
          document_match: all
    policy: exploratory
```

### Example 3: Environment-Based Policies

Different rules for development vs. production:

```yaml
policy_rules:
  # Production: strict and safe
  - name: production_strict
    priority: 100
    effect: enforce
    when:
      all:
        - field: environment
          operator: equals
          value: production
          source: user
    policy: strict_citations

  # Development: allow exploratory access
  - name: development_exploratory
    priority: 90
    effect: enforce
    when:
      all:
        - field: environment
          operator: equals
          value: development
          source: user
    policy: exploratory

  # Staging: standard policy by default
  - name: staging_standard
    priority: 80
    effect: enforce
    when:
      all:
        - field: environment
          operator: equals
          value: staging
          source: user
    policy: standard
```

### Example 4: Deny Rules with Multiple Organizations

Different denial policies for different customer tiers:

```yaml
orgs:
  - org_id: free_tier_startup
    default_policy: exploratory
    policy_rules:
      # Free tier: deny access to premium data
      - name: free_tier_no_premium
        priority: 100
        effect: deny
        when:
          any:
            - field: metadata.tier
              operator: equals
              value: premium
              source: documents
              document_match: any

      # Free tier: deny large result sets
      - name: free_tier_max_results
        priority: 90
        effect: deny
        when:
          all:
            - field: result_count
              operator: not_equals
              value: "null"
              source: user
            # Note: This is a simplified example; actual implementation
            # would need to check against a numeric threshold
      policy: exploratory

  - org_id: professional_tier
    default_policy: standard
    policy_rules:
      # Professional tier: only deny clearly unvetted sources
      - name: professional_unvetted_only
        priority: 100
        effect: deny
        when:
          any:
            - field: source
              operator: equals
              value: unvetted-web
              source: documents
              document_match: any
      policy: standard

  - org_id: enterprise_tier
    default_policy: strict_citations
    policy_rules:
      # Enterprise: no automatic denials, only policy enforcement
      # All requests pass through to policy system
```

### Example 5: Complex Multi-Condition Rules

Combining multiple conditions with AND/OR logic:

```yaml
policy_rules:
  # Deny if BOTH sensitive docs AND external user
  - name: deny_sensitive_external_user
    priority: 100
    effect: deny
    when:
      all:
        # Must be external user
        - field: org_id
          operator: equals
          value: external
          source: user
        # AND must have sensitive docs
        - field: metadata.classification
          operator: in
          value: [sensitive, confidential, pii]
          source: documents
          document_match: any

  # Enforce strict policy if ANY of these conditions
  - name: enforce_strict_if_any_risk
    priority: 80
    effect: enforce
    when:
      any:
        # Old documents
        - field: metadata.age_days
          operator: not_equals
          value: "null"
          source: documents
          document_match: any
        # Outdated sources
        - field: metadata.is_deprecated
          operator: equals
          value: "true"
          source: documents
          document_match: any
        # Unknown sources
        - field: source
          operator: not_equals
          value: verified
          source: documents
          document_match: any
    policy: strict_citations
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
3. Evaluate policy_rules in priority order (highest first)
           ↓
4. For each rule:
   - Evaluate ALL conditions in the 'when' clause
   - If conditions match:
     ├─ effect: deny → Block request, return error
     └─ effect: enforce → Apply policy, continue
           ↓
5. If no rule matched:
   - Apply organization's default_policy
           ↓
6. Execute request with chosen policy
```

### Example Execution

Given this configuration:

```yaml
orgs:
  - org_id: acme_corp
    default_policy: standard
    policy_rules:
      - name: deny_untrusted
        priority: 100
        effect: deny
        when:
          any:
            - field: source
              operator: equals
              value: untrusted
              source: documents
              document_match: any

      - name: enforce_strict_sensitive
        priority: 50
        effect: enforce
        when:
          any:
            - field: metadata.classification
              operator: equals
              value: confidential
              source: documents
              document_match: any
        policy: strict_citations
```

And this request:

```python
UserContext(
    org_id="acme_corp",
    user_id="user-1",
    role="analyst",
)
# Documents retrieved: [
#   {metadata: {classification: "confidential", source: "internal"}},
#   {metadata: {classification: "internal", source: "internal"}},
# ]
```

**Execution:**

1. ✓ Org exists: `acme_corp`
2. ✓ Priority 100 rule (`deny_untrusted`):
   - Check if ANY document has `source == untrusted`
   - Both documents have `source: internal` → No match
3. ✓ Priority 50 rule (`enforce_strict_sensitive`):
   - Check if ANY document has `classification == confidential`
   - First document has `classification: confidential` → Match!
   - Apply `strict_citations` policy
4. Request proceeds with `strict_citations` policy

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

### 1. Organize Rules by Priority Tiers

```yaml
policy_rules:
  # Tier 1: Security (100-109)
  - name: block_pii
    priority: 109

  # Tier 2: Compliance (80-99)
  - name: enforce_strict_for_confidential
    priority: 95

  # Tier 3: Business Rules (50-79)
  - name: enforce_exploratory_for_research
    priority: 60

  # Tier 4: Defaults (10-49)
  - name: enforce_default_policy
    priority: 10
```

### 2. Use Descriptive Names and Descriptions

```yaml
- name: deny_pii_external_users    # Clear what it does
  description: |
    Block external users from accessing PII-containing documents.
    Required for GDPR compliance. See GDPR requirements in wiki.
  priority: 100
  effect: deny
```

### 3. Test Conditions Against Real Data

Before deploying, verify conditions work with actual user contexts and documents:

```python
# Test that rules match expected conditions
test_cases = [
    {
        "name": "external_user_with_pii",
        "user_context": UserContext(org_id="external", role="contractor"),
        "documents": [{"metadata": {"classification": "pii"}}],
        "expected_rule": "deny_pii_external_users",
        "expected_effect": "deny",
    },
]
```

### 4. Document Rules for Audit Trails

Include rationale and references:

```yaml
- name: enforce_strict_for_regulated_data
  description: |
    Enforce strict policy for regulated data (HIPAA, GDPR, SOC2).

    Applies to:
    - Customer health information (HIPAA)
    - EU resident personal data (GDPR)
    - SOC2-classified data

    See governance policy document v2.1
    Owner: compliance-team@company.com
  priority: 100
  effect: enforce
```

### 5. Avoid Overlapping Rules

If possible, make rule conditions mutually exclusive:

```yaml
# Instead of overlapping rules:
- name: rule_a
  priority: 100
  when:
    - field: org_tier
      operator: equals
      value: enterprise

- name: rule_b
  priority: 90
  when:
    - field: org_tier
      operator: equals
      value: enterprise  # Same condition!

# Use clear non-overlapping conditions:
- name: enterprise_strict
  priority: 100
  when:
    all:
      - field: org_tier
        operator: equals
        value: enterprise
      - field: role
        operator: equals
        value: executive

- name: enterprise_exploratory
  priority: 90
  when:
    all:
      - field: org_tier
        operator: equals
        value: enterprise
      - field: role
        operator: equals
        value: analyst
```

### 6. Use Document Matching Strategically

- `document_match: any` → Deny/enforce if **any** document matches (conservative)
- `document_match: all` → Enforce only if **all** documents match (permissive)

```yaml
# Conservative: deny if ANY untrusted source
- name: deny_any_untrusted
  effect: deny
  when:
    - field: source
      operator: equals
      value: untrusted
      source: documents
      document_match: any   # Stricter

# Permissive: enforce strict only if ALL are confidential
- name: enforce_all_confidential
  effect: enforce
  when:
    - field: metadata.classification
      operator: equals
      value: confidential
      source: documents
      document_match: all   # Stricter requires all
  policy: strict_citations
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

Different policies for different customer tiers:

```yaml
policy_rules:
  - name: free_tier_exploratory
    priority: 100
    effect: enforce
    when:
      - field: org_tier
        operator: equals
        value: free
        source: user
    policy: exploratory

  - name: standard_tier_standard
    priority: 90
    effect: enforce
    when:
      - field: org_tier
        operator: equals
        value: standard
        source: user
    policy: standard

  - name: enterprise_tier_strict
    priority: 80
    effect: enforce
    when:
      - field: org_tier
        operator: equals
        value: enterprise
        source: user
    policy: strict_citations
```

### Pattern: Role-Based Access

Different access for different roles:

```yaml
policy_rules:
  - name: public_analyst_exploratory
    priority: 100
    effect: enforce
    when:
      - field: role
        operator: in
        value: [analyst, data_scientist, researcher]
        source: user
    policy: exploratory

  - name: manager_standard
    priority: 90
    effect: enforce
    when:
      - field: role
        operator: equals
        value: manager
        source: user
    policy: standard

  - name: executive_strict
    priority: 80
    effect: enforce
    when:
      - field: role
        operator: equals
        value: executive
        source: user
    policy: strict_citations
```

### Pattern: Data Sensitivity

Rules based on document classification:

```yaml
policy_rules:
  - name: deny_pii
    priority: 100
    effect: deny
    when:
      - field: metadata.classification
        operator: equals
        value: pii
        source: documents
        document_match: any

  - name: strict_for_confidential
    priority: 90
    effect: enforce
    when:
      - field: metadata.classification
        operator: equals
        value: confidential
        source: documents
        document_match: any
    policy: strict_citations

  - name: standard_for_internal
    priority: 80
    effect: enforce
    when:
      - field: metadata.classification
        operator: equals
        value: internal
        source: documents
        document_match: all
    policy: standard
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
