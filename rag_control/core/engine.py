"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pathlib import Path

from pydantic import ValidationError

from rag_control.adapters.llm import LLM
from rag_control.adapters.query_embedding import QueryEmbedding
from rag_control.adapters.vector_store import VectorStore
from rag_control.exceptions import (
    ControlPlaneConfigValidationError,
    EmbeddingModelMismatchError,
    EmbeddingModelTypeError,
    EmbeddingModelValidationError,
)
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.llm import LLMResponse, LLMStreamResponse

from .config_loader import load_control_plane_config
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
        self,
        llm: LLM,
        query_embedding: QueryEmbedding,
        vector_store: VectorStore,
        config: ControlPlaneConfig | None = None,
        config_path: str | Path | None = None,
    ) -> None:
        if config is not None and config_path is not None:
            raise ControlPlaneConfigValidationError(
                "provide either 'config' or 'config_path', not both"
            )
        if config is None and config_path is None:
            raise ControlPlaneConfigValidationError("provide one of 'config' or 'config_path'")

        self.llm = llm
        self.query_embedding = query_embedding
        self.vector_store = vector_store
        if config_path is not None:
            self.config = load_control_plane_config(config_path)
        elif config is not None:
            try:
                self.config = ControlPlaneConfig.model_validate(config)
            except ValidationError as exc:
                raise ControlPlaneConfigValidationError(
                    f"invalid control plane config: {exc}"
                ) from exc
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

    def stream(self, query: str) -> LLMStreamResponse:
        """
        Streaming public execution path.

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

        response = self.llm.stream(messages)
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
