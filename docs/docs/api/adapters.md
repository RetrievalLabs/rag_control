---
title: Adapters API Reference
description: Adapter interfaces and implementation guide
---

# Adapters API Reference

Adapters are pluggable interfaces for integrating rag_control with external services.

## LLM Adapter

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
        """
        Generate a response from a prompt.

        Args:
            prompt: The formatted prompt
            temperature: Generation temperature (0.0-2.0)
            max_tokens: Maximum output tokens

        Returns:
            GeneratedResponse with content and token counts
        """

    def stream(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Generator[GeneratedResponse, None, None]:
        """
        Stream a response from a prompt.

        Args:
            prompt: The formatted prompt
            temperature: Generation temperature (0.0-2.0)
            max_tokens: Maximum output tokens

        Yields:
            GeneratedResponse chunks as they arrive
        """
```

## Query Embedding Adapter

```python
from rag_control.core.adapters.query_embedding import QueryEmbeddingAdapter

class QueryEmbeddingAdapter:
    def embed(self, query: str) -> list[float]:
        """
        Convert query to embedding vector.

        Args:
            query: The query text

        Returns:
            List of floats representing the embedding vector
        """
```

## Vector Store Adapter

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
        """
        Search for documents similar to embedding.

        Args:
            embedding: Query embedding vector
            top_k: Number of documents to retrieve
            org_id: Optional organization ID for filtering

        Returns:
            List of retrieved documents with scores
        """
```

## Return Types

### GeneratedResponse

```python
@dataclass
class GeneratedResponse:
    content: str            # Generated text
    token_count: int        # Total tokens used
    stop_reason: str        # Why generation stopped (e.g., "end_turn", "max_tokens")
```

### RetrievedDocument

```python
@dataclass
class RetrievedDocument:
    id: str                 # Document ID
    content: str            # Document content
    metadata: dict          # Document metadata
    score: float            # Relevance score (0.0-1.0)
```

## Implementation Examples

See [Adapters Concept Guide](/concepts/adapters) for detailed implementation examples with OpenAI, Anthropic, Pinecone, and other services.

## Best Practices

1. **Error Handling**: Implement proper error handling and logging
2. **Timeout Management**: Set reasonable timeouts for external calls
3. **Caching**: Cache expensive operations when possible
4. **Testing**: Create mock adapters for testing
5. **Type Safety**: Use type hints for clarity

## See Also

- [Adapters Concept Guide](/concepts/adapters)
- [Quick Start](/getting-started/quick-start)
- [Engine API](/api/engine)
