---
title: Adapters API Reference
description: Adapter interfaces and implementation guide
---

# Adapters API Reference

Adapters are pluggable interfaces for integrating rag_control with external services. Import from `rag_control.adapters`.

## LLM

Handles text generation from prompts. Types: `ChatMessage = dict[str, str]`, `PromptInput = str | list[ChatMessage]`

**Methods:**
- `generate(prompt: PromptInput, temperature: float | None = None, max_output_tokens: int | None = None, user_context: UserContext | None = None) -> LLMResponse`
- `stream(prompt: PromptInput, temperature: float | None = None, max_output_tokens: int | None = None, user_context: UserContext | None = None) -> LLMStreamResponse`

## QueryEmbedding

Converts query text to embedding vectors.

**Properties:**
- `embedding_model: str` - Canonical embedding model identifier

**Methods:**
- `embed(query: str, user_context: UserContext | None = None) -> QueryEmbeddingResponse`

## VectorStore

Searches for documents similar to a query embedding.

**Properties:**
- `embedding_model: str` - Canonical embedding model identifier expected by this index

**Methods:**
- `search(embedding: list[float], top_k: int = 5, user_context: UserContext | None = None, filter: Filter | None = None) -> VectorStoreSearchResponse`

## Return Types

### LLMResponse

- `content: str` - Generated text
- `usage: LLMUsage` - Token counts (prompt_tokens, completion_tokens, total_tokens)
- `metadata: LLMMetadata` - Model, provider, latency_ms, request_id, timestamp, temperature, top_p, raw

### LLMStreamResponse

- `stream: Iterator[LLMStreamChunk]` - Stream of chunks (delta: str)
- `usage: LLMUsage | None` - Token counts
- `metadata: LLMMetadata | None` - Metadata

### QueryEmbeddingResponse

- `embedding: list[float]` - Embedding vector
- `metadata: QueryEmbeddingMetadata` - Model, provider, latency_ms, dimensions, request_id, timestamp, raw

### VectorStoreSearchResponse

- `records: list[VectorStoreRecord]` - Retrieved documents (id, content, score, metadata)
- `metadata: VectorStoreSearchMetadata` - Provider, index, latency_ms, top_k, returned, request_id, timestamp, raw

## Implementation Examples

See [Adapters Concept Guide](/concepts/adapters) for detailed implementation examples with OpenAI, Anthropic, Pinecone, and other services.

## See Also

- [Adapters Concept Guide](/concepts/adapters)
- [Exceptions API](/api/exceptions)
- [Engine API](/api/engine)
