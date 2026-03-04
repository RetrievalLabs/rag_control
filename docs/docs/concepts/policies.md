---
title: Policies
description: Understanding rag_control policies
---

# Policies

Policies define how the LLM should generate responses and what constraints to enforce.

## What is a Policy?

A policy is a set of rules and constraints that control:

1. **LLM Generation Parameters**: Temperature, output length, reasoning depth
2. **Citation Requirements**: Whether citations are required and validated
3. **Knowledge Restrictions**: Whether external knowledge is allowed
4. **Enforcement Checks**: What validation to perform on responses

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

### reasoning_level

Controls how much reasoning the LLM can do:

- **limited**: Minimal reasoning, direct answers from documents
- **moderate**: Balanced reasoning with some inference
- **full**: Extensive reasoning and exploration

### temperature

Controls response randomness (0.0 to 2.0):

- **0.0**: Deterministic, always the same response
- **0.7**: Default, balanced creativity and consistency
- **2.0**: Maximum randomness and creativity

Lower temperatures are good for strict policies; higher for exploratory use cases.

### require_citations

Boolean flag indicating if citations are required:

- `true`: LLM must cite document sources
- `false`: Citations optional

### allow_external_knowledge

Whether the LLM can generate content not in documents:

- `true`: Can use general knowledge
- `false`: Must stay within retrieved documents

### max_output_tokens

Maximum response length in tokens:

- Controls cost and response size
- Should match use case expectations

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

## Common Policy Patterns

### Strict Research Policy

For sensitive or highly regulated use cases:

```yaml
- name: strict_research
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

### Exploratory Policy

For brainstorming and discovery:

```yaml
- name: exploratory
  generation:
    reasoning_level: full
    allow_external_knowledge: true
    require_citations: false
    temperature: 0.9
    max_output_tokens: 2048
  enforcement:
    validate_citations: false
    block_on_missing_citations: false
    prevent_external_knowledge: false
  logging:
    level: minimal
```

### Balanced Policy

For general-purpose use:

```yaml
- name: balanced
  generation:
    reasoning_level: moderate
    allow_external_knowledge: false
    require_citations: true
    temperature: 0.3
    max_output_tokens: 1024
  enforcement:
    validate_citations: true
    block_on_missing_citations: false
    prevent_external_knowledge: true
  logging:
    level: full
```

## Policy Resolution

When a request comes in, rag_control determines which policy to apply:

1. Check organization's governance rules
2. Evaluate conditional rules (based on user context, documents, etc.)
3. If no rule matches, use organization's default policy
4. Apply policy to LLM generation

This allows fine-grained control: different policies for different users, organizations, or situations.

## Policy Validation

Policies are validated when the engine starts:

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
    print(f"Policy validation error: {e}")
```

## Best Practices

1. **Start Permissive**: Begin with loose policies, tighten over time
2. **Test Policies**: Verify policies work with your adapters
3. **Document Policies**: Use descriptions to explain the purpose
4. **Monitor Policies**: Track policy denials and enforcement
5. **Iterate**: Adjust policies based on feedback and metrics

## Examples

See the [configuration guide](/getting-started/configuration) for more policy examples.

## See Also

- [Core Concepts Overview](/concepts/overview)
- [Governance](/concepts/governance)
- [Configuration Guide](/getting-started/configuration)
