"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pathlib import Path
from typing import Any, Callable, Literal, TypeVar, cast
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
from rag_control.observability import (
    AuditLogger,
    AuditLoggingContext,
    StructlogAuditLogger,
    Tracer,
    TraceSpan,
    get_default_tracer,
)
from rag_control.policy.policy import PolicyRegistry

from ..prompt.base import PromptBuilder
from ..prompt.prompt import RAGPromptBuilder
from ..version import __version__
from .config_loader import load_control_plane_config

SDK_NAME = "rag_control"
COMPANY_NAME = "RetrievalLabs"
TRACE_SPAN_ROOT_PREFIX = "rag_control.request"
T = TypeVar("T")


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
        tracer: Tracer | None = None,
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
        self.tracer: Tracer = tracer if tracer is not None else get_default_tracer()
        self.policy_registry = PolicyRegistry(self.config)
        self.governance_registry = GovernanceRegistry(self.config)
        self.filter_registry = FilterRegistry(self.config)
        self.prompt_builder: PromptBuilder = RAGPromptBuilder()

    def run(self, query: str, user_context: UserContext) -> RunResponse:
        return cast(RunResponse, RAGControl._execute(self, query, user_context, streaming=False))

    def stream(self, query: str, user_context: UserContext) -> StreamResponse:
        return cast(
            StreamResponse,
            RAGControl._execute(self, query, user_context, streaming=True),
        )

    def _execute(
        engine: "RAGControl",
        query: str,
        user_context: UserContext,
        *,
        streaming: bool,
    ) -> RunResponse | StreamResponse:
        mode: Literal["run", "stream"] = "stream" if streaming else "run"
        request_id = str(uuid4())
        org_id = user_context.org_id
        trace_span = engine.tracer.start_span(
            engine._trace_root_span_name(mode),
            request_id=request_id,
            mode=mode,
            org_id=org_id,
            user_id=user_context.user_id,
        )
        trace_id = trace_span.trace_id
        audit_context = engine._build_audit_context(
            mode=mode,
            request_id=request_id,
            trace_id=trace_id,
            org_id=org_id,
            user_id=user_context.user_id,
        )

        try:
            audit_context.log_event("request.received")
            trace_span.event("transition.request.received")
            trace_span.event("transition.org_lookup.started")

            def _resolve_org() -> Any:
                if org_id is None:
                    error = GovernanceUserContextOrgIDRequiredError()
                    audit_context.log_event(
                        "request.denied",
                        level="warning",
                        error_type=error.__class__.__name__,
                        error_message=str(error),
                    )
                    trace_span.event(
                        "warning.request.denied",
                        error_type=error.__class__.__name__,
                        error_message=str(error),
                    )
                    raise error

                org = engine.governance_registry.get_org(org_id)
                if org is None:
                    error = GovernanceRegistryOrgNotFoundError(org_id)
                    audit_context.log_event(
                        "request.denied",
                        level="warning",
                        error_type=error.__class__.__name__,
                        error_message=str(error),
                    )
                    trace_span.event(
                        "warning.request.denied",
                        error_type=error.__class__.__name__,
                        error_message=str(error),
                    )
                    raise error
                return org

            org = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "org_lookup"),
                _resolve_org,
                org_id=org_id,
            )

            audit_context.log_event(
                "org.resolved",
                filter_name=org.filter_name,
                retrieval_top_k=org.document_policy.top_k,
            )
            trace_span.event(
                "transition.org_lookup.completed",
                filter_name=org.filter_name,
                retrieval_top_k=org.document_policy.top_k,
            )

            retrieval_filter = (
                engine.filter_registry.get(org.filter_name) if org.filter_name is not None else None
            )

            query_embedding_res = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "embedding"),
                lambda: engine.query_embedding.embed(query, user_context=user_context),
            )

            retrieve_res = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "retrieval"),
                lambda: engine.vector_store.search(
                    query_embedding_res.embedding,
                    top_k=org.document_policy.top_k,
                    user_context=user_context,
                    filter=retrieval_filter,
                ),
                top_k=org.document_policy.top_k,
            )
            docs = retrieve_res.records
            retrieved_doc_ids = [doc.id for doc in docs]

            def _resolve_policy() -> tuple[str, Any]:
                policy_name = engine.governance_registry.resolve_policy(
                    user_context=user_context,
                    source_documents=docs,
                    audit_context=audit_context,
                )
                policy = engine.policy_registry.get(policy_name)
                if policy is not None:
                    audit_context.logging_level = policy.logging.level
                return policy_name, policy

            policy_name, policy = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "policy.resolve"),
                _resolve_policy,
            )

            audit_context.log_event(
                "retrieval.completed",
                retrieved_count=len(docs),
                retrieved_doc_ids=retrieved_doc_ids,
            )
            audit_context.log_event("policy.resolved", policy_name=policy_name)

            messages = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "prompt.build"),
                lambda: engine.prompt_builder.build(
                    query=query,
                    retrieved_docs=docs,
                    policy=policy,
                ),
            )
            llm_temperature = policy.generation.temperature if policy is not None else 0.0

            llm_stage = "llm.stream" if streaming else "llm.generate"

            def _invoke_llm() -> Any:
                if streaming:
                    return engine.llm.stream(
                        messages,
                        temperature=llm_temperature,
                        user_context=user_context,
                    )
                return engine.llm.generate(
                    messages,
                    temperature=llm_temperature,
                    user_context=user_context,
                )

            response = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, llm_stage),
                _invoke_llm,
                temperature=llm_temperature,
            )

            def _enforce() -> Any:
                if streaming:
                    return engine.policy_registry.enforce_stream_response(
                        policy_name=policy_name,
                        response=response,
                        retrieved_docs=docs,
                        audit_context=audit_context,
                    )
                engine.policy_registry.enforce_response(
                    policy_name=policy_name,
                    response=response,
                    retrieved_docs=docs,
                    audit_context=audit_context,
                )
                return response

            enforced_response = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "enforcement"),
                _enforce,
                policy_name=policy_name,
            )

            if streaming:
                audit_context.log_event("enforcement.attached", policy_name=policy_name)
            else:
                audit_context.log_event("enforcement.passed", policy_name=policy_name)

            completed_fields: dict[str, Any] = {
                "policy_name": policy_name,
                "retrieved_count": len(docs),
                "retrieved_doc_ids": retrieved_doc_ids,
                "llm_model": response.metadata.model if response.metadata is not None else None,
                "llm_temperature": llm_temperature,
                "prompt_tokens": (
                    response.usage.prompt_tokens if response.usage is not None else None
                ),
                "completion_tokens": (
                    response.usage.completion_tokens if response.usage is not None else None
                ),
                "total_tokens": response.usage.total_tokens if response.usage is not None else None,
            }
            completed_fields["enforcement_attached" if streaming else "enforcement_passed"] = True
            audit_context.log_event("request.completed", **completed_fields)

            trace_span.event(
                "transition.request.completed",
                policy_name=policy_name,
                retrieved_count=len(docs),
            )
            trace_span.finish(
                status="ok",
                policy_name=policy_name,
                retrieved_count=len(docs),
                llm_model=response.metadata.model if response.metadata is not None else None,
            )

            if streaming:
                return StreamResponse(
                    policy_name=policy_name,
                    org_id=org_id,
                    user_id=user_context.user_id,
                    trace_id=trace_id,
                    filter_name=org.filter_name,
                    retrieval_top_k=org.document_policy.top_k,
                    retrieved_count=len(docs),
                    enforcement_attached=True,
                    response=enforced_response,
                )
            return RunResponse(
                policy_name=policy_name,
                org_id=org_id,
                user_id=user_context.user_id,
                trace_id=trace_id,
                filter_name=org.filter_name,
                retrieval_top_k=org.document_policy.top_k,
                retrieved_count=len(docs),
                enforcement_passed=True,
                response=enforced_response,
            )
        except Exception as exc:
            trace_span.event(
                "error.request.failed",
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            trace_span.finish(
                status="error",
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise

    def _start_child_span(self, parent_span: TraceSpan, name: str, **fields: Any) -> TraceSpan:
        return self.tracer.start_span(
            name,
            trace_id=parent_span.trace_id,
            parent_span_id=parent_span.span_id,
            **fields,
        )

    def _run_stage(
        self,
        parent_span: TraceSpan,
        name: str,
        func: Callable[[], T],
        **fields: Any,
    ) -> T:
        span = self._start_child_span(parent_span, name, **fields)
        try:
            result = func()
            span.finish(status="ok")
            return result
        except Exception as exc:
            span.finish(
                status="error",
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise

    @staticmethod
    def _trace_root_span_name(mode: Literal["run", "stream"]) -> str:
        return f"{TRACE_SPAN_ROOT_PREFIX}.{mode}"

    @staticmethod
    def _trace_stage_span_name(mode: Literal["run", "stream"], stage: str) -> str:
        return f"{TRACE_SPAN_ROOT_PREFIX}.{mode}.stage.{stage}"

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
        trace_id: str,
        org_id: str | None,
        user_id: str | None,
    ) -> AuditLoggingContext:
        return AuditLoggingContext(
            logger=self.audit_logger,
            mode=mode,
            request_id=request_id,
            trace_id=trace_id,
            org_id=org_id,
            user_id=user_id,
            sdk_name=SDK_NAME,
            sdk_version=__version__,
            company_name=COMPANY_NAME,
        )
