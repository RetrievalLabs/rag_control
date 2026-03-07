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

### Implementation Example (OpenAI)

```python
import openai
from rag_control.adapters import LLM, LLMAdapterError, ChatMessage, PromptInput
from rag_control.models import LLMResponse, LLMStreamResponse, LLMUsage, LLMMetadata, LLMStreamChunk
from rag_control.models import UserContext

class OpenAIAdapter(LLM):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    # Required abstract method implementation
    # Generates text completion from a given prompt (non-streaming)
    def generate(
        self,
        prompt: PromptInput,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        user_context: UserContext | None = None,
    ) -> LLMResponse:
        try:
            messages = self._to_messages(prompt)
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output_tokens,
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                usage=LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
                metadata=LLMMetadata(
                    model=self.model,
                    provider="openai",
                    latency_ms=0,
                    temperature=temperature,
                )
            )
        except openai.error.OpenAIError as e:
            raise LLMAdapterError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            raise LLMAdapterError(f"Unexpected error in OpenAI adapter: {str(e)}") from e

    # Required abstract method implementation
    # Generates text completion in streaming mode for real-time content delivery
    def stream(
        self,
        prompt: PromptInput,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        user_context: UserContext | None = None,
    ) -> LLMStreamResponse:
        try:
            messages = self._to_messages(prompt)
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output_tokens,
                stream=True,
            )

            def chunk_generator():
                try:
                    for chunk in response:
                        if "content" in chunk.choices[0].delta:
                            yield LLMStreamChunk(delta=chunk.choices[0].delta.content)
                except openai.error.OpenAIError as e:
                    raise LLMAdapterError(f"OpenAI streaming error: {str(e)}") from e

            return LLMStreamResponse(
                stream=chunk_generator(),
                metadata=LLMMetadata(
                    model=self.model,
                    provider="openai",
                    latency_ms=0,
                    temperature=temperature,
                )
            )
        except openai.error.OpenAIError as e:
            raise LLMAdapterError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            raise LLMAdapterError(f"Unexpected error in OpenAI adapter: {str(e)}") from e

    def _to_messages(self, prompt: PromptInput) -> list[ChatMessage]:
        """Convert string prompt to messages format."""
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        return prompt
```

## Query Embedding Adapter

The query embedding adapter converts queries to vectors for search.

### Implementation Example

```python
import openai
from rag_control.adapters import QueryEmbedding, QueryEmbeddingAdapterError
from rag_control.models.query_embedding import QueryEmbeddingResponse, QueryEmbeddingMetadata
from rag_control.models import UserContext

class OpenAIEmbeddingAdapter(QueryEmbedding):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self._embedding_model = model
        openai.api_key = api_key

    # Required abstract property implementation
    # Returns the identifier of the embedding model being used
    @property
    def embedding_model(self) -> str:
        """Return the embedding model identifier."""
        return self._embedding_model

    # Required abstract method implementation
    # Converts a query string into a vector embedding for similarity search
    def embed(
        self,
        query: str,
        user_context: UserContext | None = None,
    ) -> QueryEmbeddingResponse:
        try:
            response = openai.Embedding.create(
                input=query,
                model=self._embedding_model
            )

            return QueryEmbeddingResponse(
                embedding=response.data[0].embedding,
                metadata=QueryEmbeddingMetadata(
                    model=self._embedding_model,
                    provider="openai",
                    latency_ms=0,
                    dimensions=len(response.data[0].embedding),
                )
            )
        except openai.error.OpenAIError as e:
            raise QueryEmbeddingAdapterError(f"OpenAI embedding error: {str(e)}") from e
        except Exception as e:
            raise QueryEmbeddingAdapterError(f"Unexpected error in embedding adapter: {str(e)}") from e
```

## Vector Store Adapter

The vector store adapter retrieves documents based on query embeddings.

### Implementation Example (Pinecone)

```python
import pinecone
from rag_control.adapters import VectorStore, VectorStoreAdapterError
from rag_control.models.vector_store import VectorStoreSearchResponse, VectorStoreRecord, VectorStoreSearchMetadata
from rag_control.models import Filter
from rag_control.models import UserContext

class PineconeAdapter(VectorStore):
    def __init__(self, index_name: str, embedding_model: str):
        self.index = pinecone.Index(index_name)
        self._embedding_model = embedding_model

    # Required abstract property implementation
    # Returns the identifier of the embedding model being used
    @property
    def embedding_model(self) -> str:
        """Return the embedding model identifier."""
        return self._embedding_model

    # Required abstract method implementation
    # Searches for documents matching the query embedding and returns top results
    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        user_context: UserContext | None = None,
        filter: Filter | None = None,
    ) -> VectorStoreSearchResponse:
        try:
            # Convert Filter object to Pinecone filter format if provided
            pinecone_filter = self._filter_to_pinecone(filter) if filter else None

            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter,
            )

            records = []
            for match in results.matches:
                records.append(
                    VectorStoreRecord(
                        id=match.id,
                        content=match.metadata.get("content", ""),
                        metadata=match.metadata,
                        score=match.score,
                    )
                )

            return VectorStoreSearchResponse(
                records=records,
                metadata=VectorStoreSearchMetadata(
                    provider="pinecone",
                    index=self.index.index_name,
                    latency_ms=0,
                    top_k=top_k,
                    returned=len(records),
                )
            )
        except pinecone.PineconeException as e:
            raise VectorStoreAdapterError(f"Pinecone search error: {str(e)}") from e
        except Exception as e:
            raise VectorStoreAdapterError(f"Unexpected error in vector store adapter: {str(e)}") from e

    def _filter_to_pinecone(self, filter: Filter) -> dict:
        """Convert Filter object to Pinecone filter format."""
        # Implementation depends on Filter structure
        return {}
```

## Using Adapters

Once implemented, pass adapters to the engine:

```python
from rag_control import RAGControl

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

## Implemented Adapters

We provide production-ready adapter implementations for popular LLM and vector database providers:

### OpenAI Adapter

A high-performance adapter for OpenAI's LLM and embedding services:

- **LLM Support** - GPT models for text generation with streaming
- **Embeddings** - Text embedding models for query vectorization
- **Features** - Token tracking, latency monitoring, full OpenAI client configuration

[Learn more →](../adapters/openai-adapter)

### Pinecone Adapter

A production-ready vector database adapter for Pinecone:

- **Vector Search** - Semantic search with metadata filtering
- **Governance** - Per-user namespace isolation and access control
- **Configuration** - YAML-based policy and filter management

[Learn more →](../adapters/pinecone-adapter)

## Contributing New Adapters

We're always looking to expand our adapter ecosystem! If you've implemented an adapter for another LLM provider, embedding service, or vector database, we'd love to include it in our documentation.

**If you've created a new adapter:**

1. Follow the adapter interface patterns shown in this guide
2. Create comprehensive documentation for your adapter
3. Test your implementation thoroughly
4. **Raise a Pull Request** to add your adapter to the docs

Your contribution will help the community use rag_control with their preferred infrastructure components. Visit the [rag-control repository](https://github.com/RetrievalLabs/rag-control) to raise a PR with your adapter documentation.

## Requesting New Adapters

If you need an adapter for a specific LLM provider, embedding service, or vector database that's not yet available, please create an issue in the [rag-control repository](https://github.com/RetrievalLabs/rag-control/issues) with:

- **Provider/Service Name** - The LLM provider or database you need an adapter for
- **Use Case** - How you plan to use it with rag_control
- **Priority** - How critical this adapter is for your needs

Community contributions and feature requests help prioritize which adapters to implement next!

## See Also

- [Core Concepts Overview](/concepts/overview)
- [Quick Start](/getting-started/quick-start)
- [API Reference](/api/adapters)
