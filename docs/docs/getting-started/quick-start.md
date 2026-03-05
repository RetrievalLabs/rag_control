---
title: Quick Start
description: Get up and running with rag_control in 5 minutes
---

# Quick Start Guide

This guide will help you get rag_control running in 5 minutes.

## 1. Install rag_control

```bash
pip install rag_control
```

## 2. Create a Policy Configuration

Create a file named `policy_config.yaml`:

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

  - name: soft_research
    description: Relaxed policy for exploratory research
    generation:
      reasoning_level: full
      allow_external_knowledge: false
      require_citations: true
      temperature: 0.1
      max_output_tokens: 1024
    enforcement:
      validate_citations: true
      block_on_missing_citations: false
      prevent_external_knowledge: true
    logging:
      level: full

filters:
  - name: enterprise_only
    condition:
      field: org_tier
      operator: equals
      value: enterprise
      source: user

orgs:
  - org_id: default
    description: Default organization
    default_policy: soft_research
    document_policy:
      top_k: 5
```

## 3. Initialize the Engine

```python
from rag_control.core.engine import RAGControl
from rag_control.models.user import UserContext

# Initialize with your adapters
engine = RAGControl(
    llm=your_llm_adapter,              # Your LLM implementation
    query_embedding=your_embedding_adapter,
    vector_store=your_vector_store_adapter,
    config_path="policy_config.yaml"
)

# Create a user context
user_context = UserContext(
    org_id="default",
    user_id="user-123",
    org_tier="standard"
)
```

## 4. Run a Query

```python
# Execute a query with governance
result = engine.run(
    query="What are the key findings from our latest report?",
    user_context=user_context
)

print(f"Policy applied: {result.policy_name}")
print(f"Enforcement passed: {result.enforcement_passed}")
print(f"Response: {result.response.content}")
print(f"Tokens used: {result.response.token_count}")
```

## 5. Stream Responses (Optional)

For streaming responses:

```python
stream_result = engine.stream(
    query="Summarize the financial impact...",
    user_context=user_context
)

for chunk in stream_result.response:
    print(chunk.content, end="", flush=True)
```

## What Just Happened?

Your RAG system now has:

✅ **Policy Enforcement**: The response was validated against the `soft_research` policy
✅ **Citation Tracking**: Citations were required and verified
✅ **Audit Logging**: All requests and decisions are logged for compliance
✅ **Token Optimization**: Token usage is tracked and reported

## Implementing Adapters

You need to implement three adapter interfaces:

### LLM Adapter

```python
from rag_control.core.adapters.llm import LLMAdapter

class MyLLMAdapter(LLMAdapter):
    def __init__(self, model_name):
        self.model_name = model_name

    def generate(self, prompt, temperature, max_tokens):
        # Your LLM implementation
        pass

    def stream(self, prompt, temperature, max_tokens):
        # Your streaming implementation
        pass
```

### Query Embedding Adapter

```python
from rag_control.core.adapters.query_embedding import QueryEmbeddingAdapter

class MyEmbeddingAdapter(QueryEmbeddingAdapter):
    def embed(self, query):
        # Your embedding implementation
        pass
```

### Vector Store Adapter

```python
from rag_control.core.adapters.vector_store import VectorStoreAdapter

class MyVectorStoreAdapter(VectorStoreAdapter):
    def search(self, embedding, top_k):
        # Your vector search implementation
        pass
```

## Next Steps

- Learn more about [Core Concepts](/concepts/overview)
- Understand [Configuration](/getting-started/configuration) in detail
- Explore the [Architecture](/architecture/overview)
- Check [API Reference](/api/engine)

## Example Projects

See the `examples/` directory in the repository for complete working examples.

## Getting Help

- 📚 Read the [documentation](/)
- 🐛 Report issues on [GitHub](https://github.com/RetrievalLabs/rag_control/issues)
- 💬 Ask questions on [GitHub Discussions](https://github.com/RetrievalLabs/rag_control/discussions)
