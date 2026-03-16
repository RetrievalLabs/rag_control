"""
Copyright (c) 2026. All rights reserved.
Licensed under the Apache License 2.0.
"""

from .base import RagControlError


class AdapterError(RagControlError):
    """Base exception for adapter integration failures."""


class LLMAdapterError(AdapterError):
    """Base exception for LLM adapter failures."""


class QueryEmbeddingAdapterError(AdapterError):
    """Base exception for query embedding adapter failures."""


class VectorStoreAdapterError(AdapterError):
    """Base exception for vector store adapter failures."""
