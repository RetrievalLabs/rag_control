from abc import ABC, abstractmethod

from rag_control.models.vector_store import VectorStoreSearchResponse


class VectorStore(ABC):
    @property
    @abstractmethod
    def embedding_model(self) -> str:
        """
        Canonical embedding model identifier expected by this index.
        """
        pass

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> VectorStoreSearchResponse:
        """
        Search the vector store using an embedding and return ranked records
        with structured metadata.
        """
        pass
