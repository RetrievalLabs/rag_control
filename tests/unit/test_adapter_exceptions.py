"""
Copyright (c) 2026. All rights reserved.
Licensed under the Apache License 2.0.
"""

from rag_control.adapters import (
    AdapterError,
    LLMAdapterError,
    QueryEmbeddingAdapterError,
    VectorStoreAdapterError,
)
from rag_control.exceptions import RagControlError


def test_adapter_exceptions_are_publicly_exported() -> None:
    assert issubclass(AdapterError, RagControlError)
    assert issubclass(LLMAdapterError, AdapterError)
    assert issubclass(QueryEmbeddingAdapterError, AdapterError)
    assert issubclass(VectorStoreAdapterError, AdapterError)
