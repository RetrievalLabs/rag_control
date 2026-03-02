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
    GovernanceRegistryOrgNotFoundError,
    GovernanceUserContextOrgIDRequiredError,
)
from rag_control.filter.filter import FilterRegistry
from rag_control.governance.gov import GovernanceRegistry
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.llm import LLMResponse, LLMStreamResponse
from rag_control.models.user_context import UserContext
from rag_control.policy.policy import PolicyRegistry

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
        self._validate_embedding_model_compatibility()
        self.policy_regustry = PolicyRegistry(self.config)
        self.governance_registry = GovernanceRegistry(self.config)
        self.filter_registry = FilterRegistry(self.config)
        self.prompt_builder = RAGPromptBuilder()

    def run(self, query: str, user_context: UserContext) -> LLMResponse:
        """
        Single public execution path.

        :param query: User query to process through the RAG
        :type query: str
        """

        org_id = user_context.org_id
        if org_id is None:
            raise GovernanceUserContextOrgIDRequiredError()

        org = self.governance_registry.get_org(org_id)
        if org is None:
            raise GovernanceRegistryOrgNotFoundError(org_id)
        retrieval_filter = (
            self.filter_registry.get(org.filter_name) if org.filter_name is not None else None
        )

        query_embedding_res = self.query_embedding.embed(query, user_context=user_context)

        retrieve_res = self.vector_store.search(
            query_embedding_res.embedding,
            user_context=user_context,
            filter=retrieval_filter,
        )

        docs = retrieve_res.records
        policy_name = self.governance_registry.resolve_policy(
            user_context=user_context, source_documents=docs
        )

        policy = self.policy_regustry.get(policy_name)
        messages = self.prompt_builder.build(
            query=query,
            retrieved_docs=docs,
        )

        response = self.llm.generate(
            messages,
            temperature=policy.generation.temperature,
            user_context=user_context,
        )
        return response

    def stream(self, query: str, user_context: UserContext) -> LLMStreamResponse:
        """
        Streaming public execution path.

        :param query: User query to process through the RAG
        :type query: str
        """
        org_id = user_context.org_id
        if org_id is None:
            raise GovernanceUserContextOrgIDRequiredError()

        org = self.governance_registry.get_org(org_id)
        if org is None:
            raise GovernanceRegistryOrgNotFoundError(org_id)

        query_embedding_res = self.query_embedding.embed(query, user_context=user_context)

        retrieve_res = self.vector_store.search(
            query_embedding_res.embedding,
            user_context=user_context,
            filter=self.filter_registry.get(org.filter_name),
        )
        docs = retrieve_res.records
        self.governance_registry.resolve_policy(user_context=user_context, source_documents=docs)
        messages = self.prompt_builder.build(
            query=query,
            retrieved_docs=docs,
        )

        response = self.llm.stream(
            messages,
            user_context=user_context,
        )
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
