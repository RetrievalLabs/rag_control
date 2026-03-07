---
title: OpenAI Adapter
description: A high-performance OpenAI adapter for RAG systems providing seamless integration with rag-control framework
---

# OpenAI Adapter for RAG Control

A high-performance OpenAI adapter for RAG (Retrieval-Augmented Generation) systems, providing seamless integration with rag-control framework for LLM and embedding operations.

## Features

🚀 **High-Performance LLM Generation** - Support for chat completions with streaming
🔍 **Query Embeddings** - Generate embeddings for text queries using OpenAI's embedding models
📊 **Comprehensive Metadata** - Track latency, token usage, and request IDs
⚙️ **Flexible Configuration** - Full OpenAI client configuration support
🛡️ **Error Handling** - Robust exception handling with custom adapter errors
📝 **Type-Safe** - Full type annotations for Python static analysis

## Installation

Install the package from PyPI:

```bash
pip install openai-adapter
```

Or with uv:

```bash
uv pip install openai-adapter
```

## Version Compatibility

- **Current Stable Version:** v0.1.0
- **Compatible with:** rag-control v0.1.3

## Quick Start

### Integration with rag-control

The OpenAI Adapter is designed to integrate seamlessly with the rag-control framework:

```python
from rag_control import RAGControl
from openai_adapter import OpenAILLMAdapter, OpenAIQueryEmbeddingAdapter

# Initialize adapters
llm_adapter = OpenAILLMAdapter(api_key="sk-...")
embedding_adapter = OpenAIQueryEmbeddingAdapter(api_key="sk-...")

# Create RAG system with OpenAI adapters
rag = RAGControl(
    llm_adapter=llm_adapter,
    embedding_adapter=embedding_adapter
)

# Use for RAG operations
response = rag.query("What is machine learning?")
print(response.answer)
```

## API Reference

### OpenAILLMAdapter

```python
__init__(api_key: str, model: str = "gpt-3.5-turbo", **kwargs)
```

Initialize the LLM adapter.

**Parameters:**

- `api_key` (str): OpenAI API key for authentication
- `model` (str): Language model to use (default: gpt-3.5-turbo)
- `**kwargs`: Additional OpenAI client configuration
  - `organization` (str): Organization ID
  - `project` (str): Project ID
  - `base_url` (str): Custom API endpoint
  - `timeout` (float): Request timeout in seconds

**Raises:**

- `LLMAdapterError`: If client initialization fails

### OpenAIQueryEmbeddingAdapter

```python
__init__(api_key: str, model: str = "text-embedding-3-small", **kwargs)
```

Initialize the embedding adapter.

**Parameters:**

- `api_key` (str): OpenAI API key
- `model` (str): Embedding model (default: text-embedding-3-small)
- `**kwargs`: Additional OpenAI client configuration

**Raises:**

- `QueryEmbeddingAdapterError`: If client initialization fails

## Open Source

This project is **open source** and contributions are welcome!

- **GitHub Repository:** [RetrievalLabs/openai-adapter](https://github.com/RetrievalLabs/openai-adapter)
- **License:** Apache License 2.0

You can contribute by reporting issues, suggesting features, or submitting pull requests on GitHub.
