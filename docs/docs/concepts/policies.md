---
title: Policies
description: In-depth guide to rag_control policies, defaults, and examples
---

# Policies

Policies define how the LLM should generate responses and what constraints to enforce. They are the core mechanism for controlling LLM behavior in rag_control.

## What is a Policy?

A policy is a comprehensive set of rules and constraints that control:

1. **LLM Generation Parameters**: How the LLM generates text (temperature, output length, reasoning)
2. **Citation Requirements**: Whether sources must be cited and verified
3. **Knowledge Restrictions**: What knowledge the LLM can use
4. **Enforcement Checks**: Runtime validation of responses before returning to users
5. **Audit Logging**: What gets logged for compliance and monitoring

Every request is processed through a policy that determines the LLM's behavior and enforces constraints.

## Policy Structure

```yaml
policies:
  - name: strict_citations
    description: Strict policy with citation enforcement

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

## Generation Parameters

Generation parameters control how the LLM generates responses. They are constraints passed to the LLM before generation begins.

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `reasoning_level` | string | `limited` | `none`, `limited`, `full` | How much reasoning to show |
| `temperature` | float | `0.0` | 0.0 - 2.0 | Response randomness/creativity |
| `require_citations` | boolean | `true` | - | Whether citations are required |
| `allow_external_knowledge` | boolean | `false` | - | Can use knowledge beyond documents |
| `fallback` | string | `strict` | `strict`, `soft` | Behavior when constraints can't be met |

### reasoning_level

Controls how much reasoning the LLM includes in its response:

- **`none`**: Suppress reasoning chains, provide direct answers only
  - Best for: Concise responses, cost optimization
  - LLM skips explaining its thinking process

- **`limited` (Default)**: Brief reasoning steps, direct document-grounded answers
  - Best for: Compliance use cases, citation-heavy content
  - Shows minimal but necessary reasoning
  - Most common for strict policies

- **`full`**: Extensive reasoning, detailed exploration
  - Best for: Research, analysis, complex problem-solving
  - LLM explains thinking thoroughly
  - Higher token usage

### temperature

Controls randomness and creativity in responses (0.0 to 2.0):

- **0.0 (Default - Deterministic)**: Always produces the same response
  - Best for: Production systems requiring consistency
  - Perfect for strict policies and compliance
  - Example: "What is the capital of France?" → always "Paris"

- **0.1-0.3 (Conservative)**: Mostly consistent with minimal variation
  - Best for: Strict policies, customer service, compliance
  - Preferred for citation-heavy use cases
  - Slight natural variation while staying grounded

- **0.5-0.7 (Balanced)**: Good balance of consistency and creativity
  - Best for: General-purpose use, conversational responses
  - Maintains quality while adding natural variation

- **1.0-1.5 (Creative)**: High creativity, more varied responses
  - Best for: Content creation, brainstorming, exploration
  - Natural variation while remaining coherent

- **2.0 (Maximum)**: Highly random and creative
  - Best for: Exploratory research, ideation, creative writing
  - Risk: May be incoherent or inconsistent
  - Not recommended for production systems

**Recommendation**: Use 0.0-0.3 with strict policies (citations required), 0.5-1.0 for balanced policies.

### require_citations

Boolean flag controlling citation requirements:

- **`true` (Default)**: LLM must cite sources for claims
  - Enforces grounding in retrieved documents
  - Works with `validate_citations` enforcement
  - Helps prevent hallucinations
  - Best for: Compliance, regulated industries, accuracy-critical

- **`false`**: Citations optional
  - Better for exploratory use cases
  - Allows combining document and external knowledge without citing both
  - Suitable for brainstorming or research phases

### allow_external_knowledge

Controls whether LLM can use knowledge beyond retrieved documents:

- **`false` (Default)**: LLM restricted to retrieved documents only
  - Best for: Sensitive data, compliance, accuracy control
  - Prevents hallucinations from general knowledge
  - Enforced by `prevent_external_knowledge` check
  - Most common for secure environments

- **`true`**: LLM can combine document knowledge with general knowledge
  - Best for: Exploratory research, contextual enhancement
  - Increases flexibility but reduces control
  - Risk: May include information not in documents
  - Use when broader knowledge context is desired

### fallback

Strategy when constraints can't be satisfied:

- **`strict` (Default)**: Fail if constraints can't be met
  - Returns error/denial if policy can't be satisfied
  - Best for: Compliance, regulated environments
  - Ensures hard guarantees
  - Never compromises on requirements

- **`soft`**: Relax constraints gracefully
  - Tries to satisfy constraints, partially if needed
  - Falls back to looser constraints if necessary
  - Best for: User-facing systems needing responses
  - Better user experience but weaker guarantees

## Enforcement Checks

Enforcement validates the response after generation:

### validate_citations

Check that citations match retrieved documents:

- Verifies cited documents were actually retrieved
- Prevents hallucinated citations

### block_on_missing_citations

If `require_citations: true`, block response if citations missing:

- `true`: Deny response if not all claims are cited
- `false`: Log but don't block

### prevent_external_knowledge

Block responses containing external knowledge:

- Only if `allow_external_knowledge: false`
- Checks response against retrieved documents

### max_output_tokens

Enforce maximum response length in tokens:

- **`null` (Default)**: No limit
  - Lets LLM generate as needed
  - Flexibility but variable cost

- **512**: Short responses
  - Best for: Summaries, quick answers, FAQs
  - Cost-efficient

- **1024**: Medium responses
  - Best for: Detailed answers with balanced cost
  - Standard for most use cases

- **2048**: Long-form responses
  - Best for: Detailed analysis, research reports
  - Higher cost but more complete answers

## Policy Patterns & Examples

Different policies serve different business needs. Choose based on your use case:

### 1. Strict Compliance Policy

**Use Case**: Regulated industries, legal documents, financial compliance, healthcare

**Characteristics**:
- Zero tolerance for external knowledge
- All claims must be cited
- Deterministic responses
- Minimal token usage
- Full audit trail

```yaml
- name: strict_compliance
  description: Zero-tolerance policy for regulated environments
  generation:
    reasoning_level: limited
    allow_external_knowledge: false
    require_citations: true
    temperature: 0.0
    fallback: strict
  enforcement:
    validate_citations: true
    block_on_missing_citations: true
    prevent_external_knowledge: true
    enforce_strict_fallback: true
    max_output_tokens: 512
  logging:
    level: full
```

**Trade-offs**:
- ✅ Maximum control and auditability
- ✅ Prevents hallucinations
- ✅ Ensures citations for all claims
- ❌ May deny requests if constraints can't be met
- ❌ Limited response creativity

---

### 2. Balanced Production Policy

**Use Case**: Customer service, general Q&A, standard business applications

**Characteristics**:
- Moderate reasoning
- Citations required but soft enforcement
- Some natural variation (low temperature)
- Medium response length
- Balanced audit logging

```yaml
- name: balanced_production
  description: Balanced policy for production systems
  generation:
    reasoning_level: limited
    allow_external_knowledge: false
    require_citations: true
    temperature: 0.2
    fallback: soft
  enforcement:
    validate_citations: true
    block_on_missing_citations: false
    prevent_external_knowledge: true
    enforce_strict_fallback: false
    max_output_tokens: 1024
  logging:
    level: full
```

**Trade-offs**:
- ✅ Good user experience (soft fallback)
- ✅ Controlled responses with citations
- ✅ Practical enforcement
- ✅ Reasonable token efficiency
- ❌ May allow some external knowledge if constraints can't be met
- ❌ Less strict than compliance policies

---

### 3. Exploratory Research Policy

**Use Case**: Research, analysis, brainstorming, ideation

**Characteristics**:
- Extensive reasoning
- External knowledge allowed
- Higher creativity
- Longer responses
- Minimal enforcement

```yaml
- name: exploratory_research
  description: Permissive policy for research and analysis
  generation:
    reasoning_level: full
    allow_external_knowledge: true
    require_citations: false
    temperature: 1.2
    fallback: soft
  enforcement:
    validate_citations: false
    block_on_missing_citations: false
    prevent_external_knowledge: false
    enforce_strict_fallback: false
    max_output_tokens: 2048
  logging:
    level: minimal
```

**Trade-offs**:
- ✅ Flexible and creative responses
- ✅ Can combine document and external knowledge
- ✅ Detailed reasoning shown
- ❌ Higher hallucination risk
- ❌ No citation guarantees
- ❌ Higher token usage (cost)

---

### 4. Development/Testing Policy

**Use Case**: Development, testing, non-production environments

**Characteristics**:
- Permissive constraints
- No enforcement checks
- Minimal logging
- Fast feedback loop

```yaml
- name: development
  description: Permissive policy for development and testing
  generation:
    reasoning_level: full
    allow_external_knowledge: true
    require_citations: false
    temperature: 0.7
    fallback: soft
  enforcement:
    validate_citations: false
    block_on_missing_citations: false
    prevent_external_knowledge: false
    enforce_strict_fallback: false
    max_output_tokens: 2048
  logging:
    level: minimal
```

**Trade-offs**:
- ✅ Fastest iteration and testing
- ✅ No constraints to hinder feedback
- ❌ Not suitable for production
- ❌ Minimal audit trail

---

### 5. Premium Support Policy

**Use Case**: VIP customers, premium support tier, high-value accounts

**Characteristics**:
- Balanced with higher token limits
- Professional but flexible
- Moderate creativity
- Comprehensive responses

```yaml
- name: premium_support
  description: Premium policy for VIP customers with higher limits
  generation:
    reasoning_level: full
    allow_external_knowledge: false
    require_citations: true
    temperature: 0.5
    fallback: soft
  enforcement:
    validate_citations: true
    block_on_missing_citations: false
    prevent_external_knowledge: true
    enforce_strict_fallback: false
    max_output_tokens: 2048
  logging:
    level: full
```

**Trade-offs**:
- ✅ Comprehensive responses
- ✅ Professional quality
- ✅ Citation requirements maintained
- ✅ Good user experience
- ❌ Higher token costs
- ❌ More detailed audit logging overhead

## Policy Comparison Matrix

Quick reference for choosing the right policy:

| Aspect | Strict Compliance | Balanced Production | Exploratory | Premium | Development |
|--------|-------------------|---------------------|-------------|---------|-------------|
| **Citations Required** | Yes | Yes | No | Yes | No |
| **Temperature** | 0.0 | 0.2 | 1.2 | 0.5 | 0.7 |
| **External Knowledge** | No | No | Yes | No | Yes |
| **Max Tokens (Enforcement)** | 512 | 1024 | 2048 | 2048 | 2048 |
| **Reasoning** | Limited | Limited | Full | Full | Full |
| **Fallback** | Strict | Soft | Soft | Soft | Soft |
| **Use Case** | Compliance | General | Research | VIP | Development |
| **Hallucination Risk** | Very Low | Low | High | Low | Very High |
| **Cost** | Low | Medium | High | Very High | Medium |
| **User Experience** | Strict | Good | Flexible | Premium | Unrestricted |

---

## Policy Resolution & Governance

When a request comes in, rag_control determines which policy to apply:

### Resolution Flow

1. **Organization Lookup**: Validate user's organization exists
2. **Policy Rule Evaluation**: Check organization's policy rules in priority order
   - If rule matches with `apply_policy`: use that policy
   - If rule matches with `deny`: return denial error
3. **Default Fallback**: If no rule matches, use organization's default policy
4. **Generation**: Apply selected policy to LLM generation
5. **Enforcement**: Validate response against policy constraints

### Example Resolution

```
Request from org: "acme_corp", tier: "enterprise"
  ↓
Check policy_rules for "acme_corp" (in priority order)
  ↓
Rule 1 (priority 100): If tier=enterprise AND docs=sensitive → apply "strict_compliance"
  ✓ Matches! Use "strict_compliance" policy
  ↓
Generate with constraints: citations=required, external_knowledge=false, temp=0.0
  ↓
Enforce: validate citations, block if missing
  ↓
Return response or denial
```

This allows fine-grained control: different policies for different users, organizations, or situations without duplicating policy definitions.

## Enforcement Violations & Exceptions

When policy enforcement checks fail, rag_control raises specific exceptions to indicate what constraint was violated.

### Common Enforcement Exceptions

| Exception | When Raised | Cause | Fallback Behavior |
|-----------|-------------|-------|-------------------|
| `CitationValidationError` | `validate_citations: true` fails | Citations don't match retrieved documents | Depends on `fallback` |
| `MissingCitationsError` | `block_on_missing_citations: true` fails | Required claims lack citations | Denied (or relaxed if soft fallback) |
| `ExternalKnowledgeError` | `prevent_external_knowledge: true` fails | Response contains knowledge not in documents | Denied (or relaxed if soft fallback) |
| `MaxTokensExceededError` | Response exceeds `max_output_tokens` | LLM generated too many tokens | Truncated or denied |
| `PolicyDenialError` | Policy rule has `effect: deny` | Governance rule explicitly denies request | Request blocked immediately |
| `EnforcementError` | Generic enforcement failure | Any other constraint violation | Depends on `fallback` |

### Violation Examples

#### Citation Validation Violation

```python
# Policy requires citations
generation:
  require_citations: true
enforcement:
  validate_citations: true
  block_on_missing_citations: true

# LLM Response: "The capital is Paris (from Wikipedia)"
# Retrieved documents: Only contains "France" - no mention of Paris
# Result: CitationValidationError raised
#   - If fallback: strict → Request denied with error
#   - If fallback: soft → Constraint relaxed, try to proceed
```

#### External Knowledge Violation

```python
# Policy restricts external knowledge
generation:
  allow_external_knowledge: false
enforcement:
  prevent_external_knowledge: true

# Retrieved documents: Only about French history
# LLM Response: "Paris is the capital of France. It has a population of 2.2M
#               and is known for the Eiffel Tower (common knowledge)"
# Result: ExternalKnowledgeError raised
#   - External knowledge detected (population, Eiffel Tower not in docs)
#   - Response denied or relaxed based on fallback
```

#### Missing Citations Violation

```python
# Policy requires citations for all claims
generation:
  require_citations: true
enforcement:
  block_on_missing_citations: true

# LLM Response: "The Eiffel Tower is in Paris. It was built in 1889."
# Retrieved documents: Only first claim cited [Doc1]
# Result: MissingCitationsError raised
#   - Second claim ("built in 1889") lacks citation
#   - Response blocked or relaxed based on fallback
```

#### Token Limit Violation

```python
# Policy limits response size
enforcement:
  max_output_tokens: 512

# LLM generates 650 tokens
# Result: MaxTokensExceededError raised
#   - Response exceeds limit
#   - Typically truncated to 512 tokens
#   - If fallback: strict → May be denied entirely
```

### Fallback Behavior

How violations are handled depends on the `fallback` strategy:

#### Strict Fallback (Default)

```yaml
fallback: strict
```

- **Behavior**: Never compromise on policy requirements
- **On Violation**: Raises exception, request denied with error message
- **Best For**: Compliance, regulated environments, high-risk operations
- **Trade-off**: Better guarantees, but may deny valid requests

**Example**:
```python
try:
    result = engine.run(
        query="What is the capital?",
        user_context=user_context
    )
except PolicyDenialError as e:
    return {"error": f"Request denied: {e.message}"}
```

#### Soft Fallback

```yaml
fallback: soft
```

- **Behavior**: Try to satisfy constraints, relax if necessary
- **On Violation**: Attempts to relax constraints, retries with looser policy, returns best-effort response
- **Best For**: User-facing systems, customer service, production UX
- **Trade-off**: Better user experience, but weaker guarantees


## Policy Design Best Practices

### 1. Start Permissive, Tighten Over Time

**Principle**: Begin with loose policies in development, progressively tighten for production.

```
Development     → Exploratory policy (all parameters relaxed)
Staging         → Balanced policy (citations required, some enforcement)
Production      → Strict compliance (full enforcement)
```

**Benefits**:
- Rapid iteration in development
- Catch issues before production
- Gather data on what constraints work

### 2. Use Temperature Strategically

- **0.0**: Deterministic - good for compliance, testing
- **0.1-0.3**: Conservative - good for most production systems
- **0.5-1.0**: Balanced - good for customer-facing applications
- **1.0+**: Creative - only for research/exploratory use

**Tip**: Use lower temperatures with stricter policies, higher with exploratory policies.

### 3. Match Fallback to User Experience

```yaml
# Internal/Compliance
fallback: strict  # Better to deny than compromise

# External/Consumer
fallback: soft    # Better to relax constraints than error
```

### 4. Coordinate Citation Requirements

Always pair these together:

```yaml
# Strict coordination
require_citations: true
validate_citations: true
block_on_missing_citations: true

# Exploratory coordination
require_citations: false
validate_citations: false
prevent_external_knowledge: false
```

### 5. Document Policies Thoroughly

```yaml
- name: premium_research
  description: |-
    Premium research policy for VIP customers.
    Allows broader knowledge context with full reasoning.
    Used for custom analysis requests.
    Suitable for users: enterprise_tier, analyst_role
```

### 6. Monitor & Iterate with Metrics

Track these metrics to refine policies:

- **Denial Rate**: How often policy blocks responses
- **Token Usage**: Cost per query
- **Citation Coverage**: % of claims with citations
- **User Satisfaction**: Feedback on response quality

### 7. Organize Policies by Tier/Role

```yaml
policies:
  # Compliance tier
  - name: strict_compliance
  - name: moderate_compliance

  # Role-based
  - name: analyst_research
  - name: customer_support
  - name: executive_briefing

  # Development
  - name: development
  - name: testing
```

---

## Real-World Scenarios

### Scenario 1: Financial Services

**Requirements**: Strict compliance, auditability, accuracy

**Solution**:
1. Use `strict_compliance` policy as default
2. Higher-tier analysts get `premium_support` with more tokens
3. Research team gets `exploratory_research` for internal analysis
4. Development team uses `development` for testing

```yaml
policies:
  - name: strict_compliance
    # ... (as defined above)
  - name: premium_support
    # ... (as defined above)
  - name: exploratory_research
    # ... (as defined above)

orgs:
  - org_id: finance_corp
    default_policy: strict_compliance
    policy_rules:
      - name: premium_access
        priority: 100
        effect: allow
        apply_policy: premium_support
        when:
          all:
            - field: tier
              operator: equals
              value: premium
              source: user
```

### Scenario 2: SaaS Platform with Tiers

**Requirements**: Different policies for different subscription tiers

**Solution**:
1. Free tier: `balanced_production` (basic enforcement)
2. Pro tier: `premium_support` (more tokens, better quality)
3. Enterprise: `strict_compliance` (maximum control)

```yaml
policy_rules:
  - name: enterprise_access
    priority: 100
    effect: allow
    apply_policy: strict_compliance
    when:
      all:
        - field: subscription_tier
          operator: equals
          value: enterprise
          source: user

  - name: pro_access
    priority: 90
    effect: allow
    apply_policy: premium_support
    when:
      all:
        - field: subscription_tier
          operator: equals
          value: pro
          source: user
```

### Scenario 3: Multi-Department Organization

**Requirements**: Different policies per department

**Solution**:
- Finance: `strict_compliance` (regulatory requirements)
- Marketing: `balanced_production` (creativity within bounds)
- R&D: `exploratory_research` (innovation and discovery)

```yaml
policy_rules:
  - name: finance_strict
    priority: 100
    effect: allow
    apply_policy: strict_compliance
    when:
      all:
        - field: department
          operator: equals
          value: finance
          source: user

  - name: marketing_balanced
    priority: 90
    effect: allow
    apply_policy: balanced_production
    when:
      all:
        - field: department
          operator: equals
          value: marketing
          source: user

  - name: research_exploratory
    priority: 80
    effect: allow
    apply_policy: exploratory_research
    when:
      all:
        - field: department
          operator: equals
          value: research
          source: user
```

---

## Policy Troubleshooting

### Issue: Policy Denying All Requests

**Cause**: `fallback: strict` with impossible constraints

**Solution**: Either relax constraints or change to `fallback: soft`

### Issue: Citations Missing When Required

**Cause**: LLM not citing sources despite `require_citations: true`

**Solution**:
1. Check `temperature` isn't too high (try 0.0-0.3)
2. Verify `allow_external_knowledge: false`
3. Ensure documents are relevant for citations

### Issue: Responses Too Short

**Cause**: `max_output_tokens` set too low

**Solution**: Increase `max_output_tokens` to 1024+ for detailed responses

### Issue: High Token Usage/Cost

**Cause**: `max_output_tokens` too high or `reasoning_level: full`

**Solution**:
1. Reduce `max_output_tokens` to 512-1024
2. Use `reasoning_level: limited`
3. Use `temperature: 0.0` to prevent verbose reasoning

---

## See Also

- [Core Concepts Overview](/concepts/overview) - Understand policy context
- [Governance](/concepts/governance) - How policies are selected
- [Configuration Guide](/getting-started/configuration) - Policy syntax and examples
- [Observability](/observability/metrics) - Monitor policy metrics and performance
