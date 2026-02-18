from rag_control.adapters.llm import LLM
from rag_control.adapters.query_embedding import QueryEmbedding
from rag_control.adapters.vector_store import VectorStore
from rag_control.exceptions import (
    EmbeddingModelMismatchError,
    EmbeddingModelTypeError,
    EmbeddingModelValidationError,
)
from rag_control.models.llm import LLMResponse

from .prompt import RAGPromptBuilder


class RAGControl:
    """
    Mandatory execution spine for governed RAG.

    This class enforces:
    - Retrieval-first execution
    - RBAC filtering
    - Policy validation gates
    - Auditable lifecycle
    """

    def __init__(
        self, llm: LLM, query_embedding: QueryEmbedding, vector_store: VectorStore
    ) -> None:
        self.llm = llm
        self.query_embedding = query_embedding
        self.vector_store = vector_store
        self.prompt_builder = RAGPromptBuilder()
        self._validate_embedding_model_compatibility()

    def run(self, query: str) -> LLMResponse:
        """
        Single public execution path.

        :param query: User query to process through the RAG
        :type query: str
        """
        query_embedding_res = self.query_embedding.embed(query)

        retrieve_res = self.vector_store.search(query_embedding_res.embedding)
        docs = retrieve_res.records
        messages = self.prompt_builder.build(
            query=query,
            retrieved_docs=docs,
        )

        response = self.llm.generate(messages)
        return response

    def _validate_embedding_model_compatibility(self) -> str:
        query_model = self._normalize_embedding_model(
            self.query_embedding.embedding_model,
            "query embedding adapter model",
        )
        vector_model = self._normalize_embedding_model(
            self.vector_store.embedding_model,
            "vector store embedding model",
        )

        if query_model != vector_model:
            raise EmbeddingModelMismatchError(query_model, vector_model)

        return query_model

    @staticmethod
    def _normalize_embedding_model(model: str, source: str) -> str:
        if not isinstance(model, str):
            raise EmbeddingModelTypeError(source)

        normalized_model = model.strip()
        if not normalized_model:
            raise EmbeddingModelValidationError(source)

        return normalized_model
