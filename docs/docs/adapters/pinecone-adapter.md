---
title: Pinecone Adapter
description: A production-ready Pinecone vector database adapter that integrates with rag_control for secure, governed RAG applications
---

# Pinecone Adapter for rag_control

A production-ready Pinecone vector database adapter that integrates with rag_control for secure, governed RAG (Retrieval-Augmented Generation) applications.

## Overview

The Pinecone adapter implements the `rag_control.adapters.VectorStore` interface, enabling seamless integration of Pinecone's vector similarity search with rag_control's governance and access control framework. This enables:

- **Semantic Search** - Vector similarity-based retrieval from Pinecone
- **Metadata Filtering** - Rich filtering support with AND/OR logic
- **Access Control** - Per-user namespace isolation via user context
- **Governance** - Full compliance with rag_control's security and audit framework
- **Error Handling** - Graceful error management with detailed diagnostics

## Installation

Install the package via pip:

```bash
pip install pinecone-adapter
```

Or using uv:

```bash
uv pip install pinecone-adapter
```


## Quick Start

### 1. Initialize the Adapter

```python
from pinecone_adapter import PineconeVectorStoreAdapter

adapter = PineconeVectorStoreAdapter(
    api_key="your-pinecone-api-key",
    index_name="your-index-name",
    embedding_model="text-embedding-3-small"
)
```

## Integration with rag_control

### Complete RAG Pipeline Example

```python
from pinecone_adapter import PineconeVectorStoreAdapter
from rag_control import RAGControl
from rag_control.models import UserContext

# 1. Initialize adapters
vector_store = PineconeVectorStoreAdapter(
    api_key="your-pinecone-api-key",
    index_name="documents",
    embedding_model="text-embedding-3-small"
)

# Import or implement your embedding and LLM adapters
from your_embedding_provider import OpenAIEmbeddingAdapter
from your_llm_provider import OpenAIAdapter

query_embedding = OpenAIEmbeddingAdapter(
    api_key="your-openai-api-key",
    model="text-embedding-3-small"
)

llm = OpenAIAdapter(
    api_key="your-openai-api-key",
    model="gpt-4"
)

# 2. Configure rag_control - Load from YAML
rag_control = RAGControl(
    llm=llm,
    query_embedding=query_embedding,
    vector_store=vector_store,
    config_path="rag_control_config.yaml"
)

# 3. Run a query
user_context = UserContext(
    user_id="user123",
    org_id="org456",
    attributes={"namespace": "department-finance"}
)

response = rag_control.run(
    query="What are our Q1 financial results?",
    user_context=user_context
)

print(response.response.text)
print(f"Retrieved {response.retrieved_count} documents")
print(f"Policy applied: {response.policy_name}")
```

### Streaming Responses

```python
# Stream responses for real-time output
stream_response = rag_control.stream(
    query="What are our Q1 financial results?",
    user_context=user_context
)

# Response includes enforcement metadata
print(f"Enforcement attached: {stream_response.enforcement_attached}")

for chunk in stream_response.response:
    print(chunk.text, end="", flush=True)
```

## Metadata Filtering

The adapter supports all rag_control filter operators:

| Operator | Description |
|----------|-------------|
| equals | Exact value match |
| in | Value in list |
| lt | Less than |
| lte | Less than or equal |
| gt | Greater than |
| gte | Greater than or equal |
| exists | Field exists |
| intersects | Array intersection (approximated as in) |

The selected filter is applied based on the org's `document_policy.filter_name`.

## YAML Configuration File

For production deployments, use YAML config files:

```yaml
# rag_control_config.yaml
orgs:
  - org_id: org456
    document_policy:
      filter_name: published
      top_k: 10
    default_policy: default
    policy_rules: []

filters:
  - name: published
    condition:
      field: status
      operator: equals
      value: published

  - name: finance_2024
    and:
      - condition:
          field: department
          operator: equals
          value: finance
      - condition:
          field: year
          operator: gte
          value: 2024

policies:
  - name: default
    generation:
      temperature: 0.7
      filter_name: finance_2024
    enforcement:
      max_output_tokens: 2048
```

## Namespace Isolation

Use `user_context.attributes["namespace"]` to isolate results per user or tenant:

```python
# Different users see different results
user_context_1 = UserContext(
    user_id="user1",
    org_id="org456",
    attributes={"namespace": "user1"}
)

user_context_2 = UserContext(
    user_id="user2",
    org_id="org456",
    attributes={"namespace": "user2"}
)

response_1 = adapter.search(embedding=query_embedding, user_context=user_context_1)
response_2 = adapter.search(embedding=query_embedding, user_context=user_context_2)
```

If no namespace is specified, the search defaults to an empty namespace (all documents).

## API Reference

### PineconeVectorStoreAdapter

#### Constructor

```python
PineconeVectorStoreAdapter(
    api_key: str,
    index_name: str,
    embedding_model: str
)
```

**Parameters:**

- `api_key` - Pinecone API key
- `index_name` - Name of Pinecone index to query
- `embedding_model` - Embedding model identifier (e.g., "text-embedding-3-small")

**Raises:**

- `VectorStoreAdapterError` - If index doesn't exist or API key is invalid

#### embedding_model Property

```python
model: str = adapter.embedding_model
```

Returns the embedding model identifier. Must match the embedding model in your query embedding adapter.

#### search() Method

```python
response = adapter.search(
    embedding: list[float],
    top_k: int = 5,
    user_context: UserContext | None = None,
    filter: Filter | None = None
) -> VectorStoreSearchResponse
```

**Parameters:**

- `embedding` - Query embedding vector
- `top_k` - Number of results (default: 5). In rag_control, controlled by org's `document_policy.top_k`
- `user_context` - User context with `org_id`, `user_id`, and optional attributes
- `filter` - Metadata filter. In rag_control, provided by filter registry

**Returns:**

`VectorStoreSearchResponse` with:
- `records` - List of VectorStoreRecord objects
- `metadata` - VectorStoreSearchMetadata with latency, provider, etc.

**Raises:**

- `VectorStoreAdapterError` - If search fails

## Error Handling

```python
from rag_control.exceptions import VectorStoreAdapterError

try:
    response = adapter.search(embedding=query_embedding)
except VectorStoreAdapterError as e:
    print(f"Search failed: {e}")
```

## Open Source

This project is **open source** and contributions are welcome!

- **GitHub Repository:** [RetrievalLabs/pinecone-adapter](https://github.com/RetrievalLabs/pinecone-adapter)
- **License:** Apache License 2.0

You can contribute by reporting issues, suggesting features, or submitting pull requests on GitHub.
