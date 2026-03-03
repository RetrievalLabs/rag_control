"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pathlib import Path
from typing import Literal
from uuid import uuid4

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
from rag_control.models.run import RunResponse, StreamResponse
from rag_control.models.user_context import UserContext
from rag_control.observability import AuditLogger, AuditLoggingContext, StructlogAuditLogger
from rag_control.policy.policy import PolicyRegistry

from ..prompt.base import PromptBuilder
from ..prompt.prompt import RAGPromptBuilder
from ..version import __version__
from .config_loader import load_control_plane_config

SDK_NAME = "rag_control"
COMPANY_NAME = "RetrievalLabs"


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
        audit_logger: AuditLogger | None = None,
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
        self.audit_logger: AuditLogger = (
            audit_logger if audit_logger is not None else StructlogAuditLogger()
        )
        self.policy_registry = PolicyRegistry(self.config)
        self.governance_registry = GovernanceRegistry(self.config)
        self.filter_registry = FilterRegistry(self.config)
        self.prompt_builder: PromptBuilder = RAGPromptBuilder()

    def run(self, query: str, user_context: UserContext) -> RunResponse:
        """
        Single public execution path.

        :param query: User query to process through the RAG
        :type query: str
        """
        request_id = str(uuid4())
        org_id = user_context.org_id
        audit_context = self._build_audit_context(
            mode="run",
            request_id=request_id,
            org_id=org_id,
            user_id=user_context.user_id,
        )

        audit_context.log_event("request.received")
        if org_id is None:
            error = GovernanceUserContextOrgIDRequiredError()
            audit_context.log_event(
                "request.denied",
                level="warning",
                error_type=error.__class__.__name__,
                error_message=str(error),
            )
            raise error

        org = self.governance_registry.get_org(org_id)
        if org is None:
            error = GovernanceRegistryOrgNotFoundError(org_id)
            audit_context.log_event(
                "request.denied",
                level="warning",
                error_type=error.__class__.__name__,
                error_message=str(error),
            )
            raise error

        audit_context.log_event(
            "org.resolved",
            filter_name=org.filter_name,
            retrieval_top_k=org.document_policy.top_k,
        )
        retrieval_filter = (
            self.filter_registry.get(org.filter_name) if org.filter_name is not None else None
        )

        query_embedding_res = self.query_embedding.embed(query, user_context=user_context)

        retrieve_res = self.vector_store.search(
            query_embedding_res.embedding,
            top_k=org.document_policy.top_k,
            user_context=user_context,
            filter=retrieval_filter,
        )
        docs = retrieve_res.records
        retrieved_doc_ids = [doc.id for doc in docs]

        policy_name = self.governance_registry.resolve_policy(
            user_context=user_context,
            source_documents=docs,
            audit_context=audit_context,
        )
        policy = self.policy_registry.get(policy_name)
        if policy is not None:
            audit_context.logging_level = policy.logging.level

        audit_context.log_event(
            "retrieval.completed",
            retrieved_count=len(docs),
            retrieved_doc_ids=retrieved_doc_ids,
        )
        audit_context.log_event("policy.resolved", policy_name=policy_name)
        messages = self.prompt_builder.build(
            query=query,
            retrieved_docs=docs,
            policy=policy,
        )
        llm_temperature = policy.generation.temperature if policy is not None else 0.0

        response = self.llm.generate(
            messages,
            temperature=llm_temperature,
            user_context=user_context,
        )

        self.policy_registry.enforce_response(
            policy_name=policy_name,
            response=response,
            retrieved_docs=docs,
            audit_context=audit_context,
        )
        audit_context.log_event("enforcement.passed", policy_name=policy_name)
        audit_context.log_event(
            "request.completed",
            policy_name=policy_name,
            retrieved_count=len(docs),
            retrieved_doc_ids=retrieved_doc_ids,
            llm_model=response.metadata.model,
            llm_temperature=llm_temperature,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            enforcement_passed=True,
        )
        return RunResponse(
            policy_name=policy_name,
            org_id=org_id,
            user_id=user_context.user_id,
            filter_name=org.filter_name,
            retrieval_top_k=org.document_policy.top_k,
            retrieved_count=len(docs),
            enforcement_passed=True,
            response=response,
        )

    def stream(self, query: str, user_context: UserContext) -> StreamResponse:
        """
        Streaming public execution path.

        :param query: User query to process through the RAG
        :type query: str
        """
        request_id = str(uuid4())
        org_id = user_context.org_id
        audit_context = self._build_audit_context(
            mode="stream",
            request_id=request_id,
            org_id=org_id,
            user_id=user_context.user_id,
        )

        audit_context.log_event("request.received")
        if org_id is None:
            error = GovernanceUserContextOrgIDRequiredError()
            audit_context.log_event(
                "request.denied",
                level="warning",
                error_type=error.__class__.__name__,
                error_message=str(error),
            )
            raise error

        org = self.governance_registry.get_org(org_id)
        if org is None:
            error = GovernanceRegistryOrgNotFoundError(org_id)
            audit_context.log_event(
                "request.denied",
                level="warning",
                error_type=error.__class__.__name__,
                error_message=str(error),
            )
            raise error

        audit_context.log_event(
            "org.resolved",
            filter_name=org.filter_name,
            retrieval_top_k=org.document_policy.top_k,
        )

        query_embedding_res = self.query_embedding.embed(query, user_context=user_context)

        retrieve_res = self.vector_store.search(
            query_embedding_res.embedding,
            top_k=org.document_policy.top_k,
            user_context=user_context,
            filter=self.filter_registry.get(org.filter_name),
        )
        docs = retrieve_res.records
        retrieved_doc_ids = [doc.id for doc in docs]

        policy_name = self.governance_registry.resolve_policy(
            user_context=user_context,
            source_documents=docs,
            audit_context=audit_context,
        )
        policy = self.policy_registry.get(policy_name)
        if policy is not None:
            audit_context.logging_level = policy.logging.level

        audit_context.log_event(
            "retrieval.completed",
            retrieved_count=len(docs),
            retrieved_doc_ids=retrieved_doc_ids,
        )
        audit_context.log_event("policy.resolved", policy_name=policy_name)
        messages = self.prompt_builder.build(
            query=query,
            retrieved_docs=docs,
            policy=policy,
        )
        llm_temperature = policy.generation.temperature if policy is not None else 0.0

        response = self.llm.stream(
            messages,
            temperature=llm_temperature,
            user_context=user_context,
        )
        enforced_response = self.policy_registry.enforce_stream_response(
            policy_name=policy_name,
            response=response,
            retrieved_docs=docs,
            audit_context=audit_context,
        )
        audit_context.log_event("enforcement.attached", policy_name=policy_name)
        audit_context.log_event(
            "request.completed",
            policy_name=policy_name,
            retrieved_count=len(docs),
            retrieved_doc_ids=retrieved_doc_ids,
            llm_model=response.metadata.model if response.metadata is not None else None,
            llm_temperature=llm_temperature,
            prompt_tokens=response.usage.prompt_tokens if response.usage is not None else None,
            completion_tokens=(
                response.usage.completion_tokens if response.usage is not None else None
            ),
            total_tokens=response.usage.total_tokens if response.usage is not None else None,
            enforcement_attached=True,
        )
        return StreamResponse(
            policy_name=policy_name,
            org_id=org_id,
            user_id=user_context.user_id,
            filter_name=org.filter_name,
            retrieval_top_k=org.document_policy.top_k,
            retrieved_count=len(docs),
            enforcement_passed=True,
            response=enforced_response,
        )

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

    def _build_audit_context(
        self,
        *,
        mode: Literal["run", "stream"],
        request_id: str,
        org_id: str | None,
        user_id: str | None,
    ) -> AuditLoggingContext:
        return AuditLoggingContext(
            logger=self.audit_logger,
            mode=mode,
            request_id=request_id,
            org_id=org_id,
            user_id=user_id,
            sdk_name=SDK_NAME,
            sdk_version=__version__,
            company_name=COMPANY_NAME,
        )
