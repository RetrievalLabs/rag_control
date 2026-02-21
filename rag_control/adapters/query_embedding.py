"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from abc import ABC, abstractmethod

from rag_control.models.query_embedding import QueryEmbeddingResponse
from rag_control.models.user_context import UserContext


class QueryEmbedding(ABC):
    @property
    @abstractmethod
    def embedding_model(self) -> str:
        """
        Canonical embedding model identifier used by this adapter.
        """
        pass

    @abstractmethod
    def embed(self, query: str, user_context: UserContext | None = None) -> QueryEmbeddingResponse:
        """
        Generate a vector embedding for a single query string.
        Must return embedding values with structured metadata.
        """
        pass
