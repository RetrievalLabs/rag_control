---
title: Adapters
description: Understanding rag_control adapters
---

# Adapters

Adapters are the pluggable interfaces that connect rag_control to your infrastructure components.

## What are Adapters?

Adapters abstract the interaction with:

- **LLM**: Language models for generation
- **Query Embedding**: Converting queries to vectors
- **Vector Store**: Storing and searching documents

This design allows you to use rag_control with any LLM provider or vector database.

## Adapter Architecture

```
rag_control Engine
    ↓
    ├─→ LLM Adapter → Your LLM (OpenAI, Anthropic, etc.)
    ├─→ Query Embedding Adapter → Your Embeddings (OpenAI, Cohere, etc.)
    └─→ Vector Store Adapter → Your Database (Pinecone, Weaviate, etc.)
```

## LLM Adapter

The LLM adapter handles text generation.

### Interface

```python
from rag_control.core.adapters.llm import LLMAdapter
from rag_control.models.response import GeneratedResponse

class LLMAdapter:
    def generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> GeneratedResponse:
        """Generate a response from a prompt."""
        pass

    def stream(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Generator[GeneratedResponse, None, None]:
        """Stream a response from a prompt."""
        pass
```

### Implementation Example (OpenAI)

```python
import openai
from rag_control.core.adapters.llm import LLMAdapter
from rag_control.models.response import GeneratedResponse

class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    def generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> GeneratedResponse:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return GeneratedResponse(
            content=response.choices[0].message.content,
            token_count=response.usage.total_tokens,
            stop_reason="end_turn"
        )

    def stream(self, prompt, temperature, max_tokens):
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in response:
            if "content" in chunk.choices[0].delta:
                yield GeneratedResponse(
                    content=chunk.choices[0].delta.content,
                    token_count=0,  # Updated in batch
                    stop_reason=None
                )
```

## Query Embedding Adapter

The query embedding adapter converts queries to vectors for search.

### Interface

```python
from rag_control.core.adapters.query_embedding import QueryEmbeddingAdapter

class QueryEmbeddingAdapter:
    def embed(self, query: str) -> list[float]:
        """Convert query to embedding vector."""
        pass
```

### Implementation Example

```python
import openai
from rag_control.core.adapters.query_embedding import QueryEmbeddingAdapter

class OpenAIEmbeddingAdapter(QueryEmbeddingAdapter):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    def embed(self, query: str) -> list[float]:
        response = openai.Embedding.create(
            input=query,
            model=self.model
        )
        return response.data[0].embedding
```

## Vector Store Adapter

The vector store adapter retrieves documents based on query embeddings.

### Interface

```python
from rag_control.core.adapters.vector_store import VectorStoreAdapter
from rag_control.models.document import RetrievedDocument

class VectorStoreAdapter:
    def search(
        self,
        embedding: list[float],
        top_k: int,
        org_id: str | None = None,
    ) -> list[RetrievedDocument]:
        """Search for documents similar to embedding."""
        pass
```

### Implementation Example (Pinecone)

```python
import pinecone
from rag_control.core.adapters.vector_store import VectorStoreAdapter
from rag_control.models.document import RetrievedDocument

class PineconeAdapter(VectorStoreAdapter):
    def __init__(self, index_name: str):
        self.index = pinecone.Index(index_name)

    def search(
        self,
        embedding: list[float],
        top_k: int,
        org_id: str | None = None,
    ) -> list[RetrievedDocument]:
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )

        documents = []
        for match in results.matches:
            documents.append(
                RetrievedDocument(
                    id=match.id,
                    content=match.metadata.get("content", ""),
                    metadata=match.metadata,
                    score=match.score,
                )
            )
        return documents
```

## Using Adapters

Once implemented, pass adapters to the engine:

```python
from rag_control.core.engine import RAGControl

llm = OpenAIAdapter(api_key="sk-...")
embedding = OpenAIEmbeddingAdapter(api_key="sk-...")
vector_store = PineconeAdapter(index_name="documents")

engine = RAGControl(
    llm=llm,
    query_embedding=embedding,
    vector_store=vector_store,
    config_path="policy_config.yaml"
)
```

## Adapter Guidelines

### Error Handling

Adapters should handle errors gracefully:

```python
class RobustLLMAdapter(LLMAdapter):
    def generate(self, prompt, temperature, max_tokens):
        try:
            # Call LLM
            response = self.llm_client.generate(...)
            return response
        except Exception as e:
            # Log and re-raise
            logger.error(f"LLM generation failed: {e}")
            raise
```

### Performance Considerations

- Cache embeddings when possible
- Batch operations for efficiency
- Use connection pooling for external services

### Testing Adapters

Mock adapters for testing:

```python
from rag_control.core.adapters.llm import LLMAdapter

class MockLLMAdapter(LLMAdapter):
    def generate(self, prompt, temperature, max_tokens):
        return GeneratedResponse(
            content="Mock response",
            token_count=2,
            stop_reason="end_turn"
        )

    def stream(self, prompt, temperature, max_tokens):
        yield GeneratedResponse(
            content="Mock ",
            token_count=0,
            stop_reason=None
        )
        yield GeneratedResponse(
            content="response",
            token_count=0,
            stop_reason="end_turn"
        )
```

## Common Adapters

Ready-made adapters for popular services:

| Service | Adapter | Link |
|---------|---------|------|
| OpenAI | `OpenAIAdapter` | [OpenAI API](https://openai.com/) |
| Anthropic | `AnthropicAdapter` | [Anthropic API](https://www.anthropic.com/) |
| Pinecone | `PineconeAdapter` | [Pinecone](https://www.pinecone.io/) |
| Weaviate | `WeaviateAdapter` | [Weaviate](https://weaviate.io/) |

Check the examples directory for more implementations.

## Best Practices

1. **Handle Errors**: Implement proper error handling in adapters
2. **Log Calls**: Log adapter calls for debugging
3. **Implement Caching**: Cache expensive operations when possible
4. **Test Thoroughly**: Test adapters with mock data
5. **Type Safety**: Use type hints for clarity

## See Also

- [Core Concepts Overview](/concepts/overview)
- [Quick Start](/getting-started/quick-start)
- [Architecture](/architecture/overview)
