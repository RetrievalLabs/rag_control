"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
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
