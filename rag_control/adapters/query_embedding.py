from abc import ABC, abstractmethod

from rag_control.models.query_embedding import QueryEmbeddingResponse


class QueryEmbedding(ABC):
    @abstractmethod
    def embed(self, query: str) -> QueryEmbeddingResponse:
        """
        Generate a vector embedding for a single query string.
        Must return embedding values with structured metadata.
        """
        pass
