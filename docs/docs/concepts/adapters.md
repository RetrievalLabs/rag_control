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
from typing import Generator
from rag_control.core.adapters import LLMAdapter
from rag_control.models import GeneratedResponse
from rag_control.models import UserContext

class LLMAdapter:
    def generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        user_context: UserContext | None = None,
    ) -> GeneratedResponse:
        """Generate a response from a prompt.

        Args:
            prompt: The input text to generate a response for.
            temperature: Sampling temperature (0.0-1.0). Higher values increase
                randomness, lower values make output more deterministic.
            max_tokens: Maximum number of tokens to generate in the response.
            user_context: Optional user context for user-aware generation behavior.

        Returns:
            GeneratedResponse: The generated response with content and token metadata.
        """
        pass

    def stream(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        user_context: UserContext | None = None,
    ) -> Generator[GeneratedResponse, None, None]:
        """Stream a response from a prompt in chunks.

        Args:
            prompt: The input text to generate a response for.
            temperature: Sampling temperature (0.0-1.0). Higher values increase
                randomness, lower values make output more deterministic.
            max_tokens: Maximum number of tokens to generate in the response.
            user_context: Optional user context for user-aware generation behavior.

        Yields:
            GeneratedResponse: Response chunks as they become available.
        """
        pass
```

### Implementation Example (OpenAI)

```python
import openai
from rag_control.core.adapters import LLMAdapter
from rag_control.models import GeneratedResponse
from rag_control.models import UserContext

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
        user_context: UserContext | None = None,
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

    def stream(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        user_context: UserContext | None = None,
    ):
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
from rag_control.core.adapters import QueryEmbeddingAdapter
from rag_control.models import UserContext

class QueryEmbeddingAdapter:
    def embed(
        self,
        query: str,
        user_context: UserContext | None = None,
    ) -> list[float]:
        """Convert query to embedding vector.

        Args:
            query: The text to embed.
            user_context: Optional user context for user-aware embedding behavior.

        Returns:
            list[float]: The embedding vector.
        """
        pass
```

### Implementation Example

```python
import openai
from rag_control.core.adapters import QueryEmbeddingAdapter
from rag_control.models import UserContext

class OpenAIEmbeddingAdapter(QueryEmbeddingAdapter):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    def embed(
        self,
        query: str,
        user_context: UserContext | None = None,
    ) -> list[float]:
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
from rag_control.models import UserContext

class VectorStoreAdapter:
    def search(
        self,
        embedding: list[float],
        top_k: int,
        user_context: UserContext | None = None,
        filter: dict | None = None,
    ) -> list[RetrievedDocument]:
        """Search for documents similar to embedding.

        Args:
            embedding: The query embedding vector to search with.
            top_k: Maximum number of documents to return.
            user_context: Optional user context for user-scoped retrieval behavior.
            filter: Optional metadata filter for document selection.

        Returns:
            list[RetrievedDocument]: Retrieved documents ranked by similarity.
        """
        pass
```

### Implementation Example (Pinecone)

```python
import pinecone
from rag_control.core.adapters.vector_store import VectorStoreAdapter
from rag_control.models.document import RetrievedDocument
from rag_control.models import UserContext

class PineconeAdapter(VectorStoreAdapter):
    def __init__(self, index_name: str):
        self.index = pinecone.Index(index_name)

    def search(
        self,
        embedding: list[float],
        top_k: int,
        user_context: UserContext | None = None,
        filter: dict | None = None,
    ) -> list[RetrievedDocument]:
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter,
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


## See Also

- [Core Concepts Overview](/concepts/overview)
- [Quick Start](/getting-started/quick-start)
- [API Reference](/api/adapters)
