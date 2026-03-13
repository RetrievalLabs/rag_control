"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

import time
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
from rag_control.models.org import OrgConfig
from rag_control.models.policy import Policy
from rag_control.models.run import RunResponse, StreamResponse
from rag_control.models.user_context import UserContext
from rag_control.observability import (
    AuditLogger,
    AuditLoggingContext,
    MetricsRecorder,
    StructlogAuditLogger,
    Tracer,
    TraceSpan,
    get_default_metrics_recorder,
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
        metrics_recorder: MetricsRecorder | None = None,
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
        self.metrics_recorder: MetricsRecorder = (
            metrics_recorder if metrics_recorder is not None else get_default_metrics_recorder()
        )
        self.policy_registry = PolicyRegistry(self.config, self.metrics_recorder)
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
        request_started_at = time.perf_counter()
        trace_span = engine.tracer.start_span(
            engine._trace_root_span_name(mode),
            request_id=request_id,
            mode=mode,
            span_kind="internal",
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

            def _resolve_org() -> OrgConfig:
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
                success_fields=lambda resolved_org: {
                    "org_id": resolved_org.org_id,
                },
                metrics_labels={"mode": mode, "stage": "org_lookup", "org_id": org_id or ""},
                org_id=org_id,
            )

            audit_context.log_event(
                "org.resolved",
            )

            trace_span.event(
                "transition.org_lookup.completed",
                org_id=org.org_id,
            )

            def _resolve_policy() -> Policy:
                policy_name = engine.governance_registry.resolve_policy(
                    user_context=user_context,
                    audit_context=audit_context,
                )
                policy = engine.policy_registry.get(policy_name)
                audit_context.logging_level = policy.logging.level
                return policy

            policy = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "policy.resolve"),
                _resolve_policy,
                success_fields=lambda resolved_policy: {
                    "policy_name": resolved_policy.name,
                },
                metrics_labels={"mode": mode, "stage": "policy.resolve", "org_id": org_id or ""},
                org_id=org_id,
            )

            policy_name = policy.name
            audit_context.log_event(
                "policy.resolved",
                policy_name=policy_name,
                top_k=policy.document_policy.top_k,
                filter_name=policy.document_policy.filter_name,
            )

            retrieval_filter = (
                engine.filter_registry.get(policy.document_policy.filter_name)
                if policy.document_policy.filter_name is not None
                else None
            )

            query_embedding_res = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "embedding"),
                lambda: engine.query_embedding.embed(query, user_context=user_context),
                success_fields=lambda embedding_res: {
                    "embedding_model": embedding_res.metadata.model,
                    "embedding_dimensions": embedding_res.metadata.dimensions,
                },
                metrics_labels={"mode": mode, "stage": "embedding", "org_id": org_id or ""},
            )
            # Record embedding model-specific metrics
            embedding_model = (
                query_embedding_res.metadata.model
                if query_embedding_res.metadata is not None
                else "unknown"
            )
            embedding_dims = (
                query_embedding_res.metadata.dimensions
                if query_embedding_res.metadata is not None
                else 0
            )
            engine.metrics_recorder.record(
                "rag_control.embedding.dimensions",
                float(embedding_dims),
                kind="histogram",
                mode=mode,
                org_id=org_id or "",
                model=embedding_model,
            )

            retrieve_res = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "retrieval"),
                lambda: engine.vector_store.search(
                    query_embedding_res.embedding,
                    top_k=policy.document_policy.top_k,
                    user_context=user_context,
                    filter=retrieval_filter,
                ),
                success_fields=lambda search_res: {
                    "vector_index": search_res.metadata.index,
                    "returned": search_res.metadata.returned,
                },
                metrics_labels={"mode": mode, "stage": "retrieval", "org_id": org_id or ""},
                top_k=policy.document_policy.top_k,
            )
            docs = retrieve_res.records
            retrieved_doc_ids = [doc.id for doc in docs]

            audit_context.log_event(
                "retrieval.completed",
                retrieved_count=len(docs),
                retrieved_doc_ids=retrieved_doc_ids,
            )

            engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "resolve_deny"),
                lambda: engine.governance_registry.resolve_deny(
                    user_context=user_context,
                    source_documents=docs,
                    audit_context=audit_context,
                ),
                metrics_labels={"mode": mode, "stage": "resolve_deny", "org_id": org_id or ""},
            )

            messages = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, "prompt.build"),
                lambda: engine.prompt_builder.build(
                    query=query,
                    retrieved_docs=docs,
                    policy=policy,
                ),
                success_fields=lambda prompt_messages: {"message_count": len(prompt_messages)},
                metrics_labels={"mode": mode, "stage": "prompt.build", "org_id": org_id or ""},
            )
            llm_temperature = policy.generation.temperature if policy is not None else 0.0
            llm_max_output_tokens = (
                policy.enforcement.max_output_tokens if policy is not None else None
            )

            llm_stage = "llm.stream" if streaming else "llm.generate"

            def _invoke_llm() -> Any:
                if streaming:
                    return engine.llm.stream(
                        messages,
                        temperature=llm_temperature,
                        max_output_tokens=llm_max_output_tokens,
                        user_context=user_context,
                    )
                return engine.llm.generate(
                    messages,
                    temperature=llm_temperature,
                    max_output_tokens=llm_max_output_tokens,
                    user_context=user_context,
                )

            response = engine._run_stage(
                trace_span,
                engine._trace_stage_span_name(mode, llm_stage),
                _invoke_llm,
                success_fields=lambda llm_res: {
                    "llm_model": llm_res.metadata.model if llm_res.metadata is not None else None,
                    "prompt_tokens": (
                        llm_res.usage.prompt_tokens if llm_res.usage is not None else None
                    ),
                    "completion_tokens": (
                        llm_res.usage.completion_tokens if llm_res.usage is not None else None
                    ),
                    "total_tokens": (
                        llm_res.usage.total_tokens if llm_res.usage is not None else None
                    ),
                },
                metrics_labels={"mode": mode, "stage": llm_stage, "org_id": org_id or ""},
                temperature=llm_temperature,
                max_output_tokens=llm_max_output_tokens,
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
                metrics_labels={"mode": mode, "stage": "enforcement", "org_id": org_id or ""},
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
                "llm_max_output_tokens": llm_max_output_tokens,
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

            # Record request metrics on success
            request_duration_ms = (time.perf_counter() - request_started_at) * 1000
            engine.metrics_recorder.record(
                "rag_control.requests",
                1.0,
                kind="counter",
                mode=mode,
                org_id=org_id or "",
                status="ok",
            )
            engine.metrics_recorder.record(
                "rag_control.request.duration_ms",
                request_duration_ms,
                kind="histogram",
                unit="ms",
                mode=mode,
                org_id=org_id or "",
                status="ok",
            )
            # Record retrieval metrics
            engine.metrics_recorder.record(
                "rag_control.retrieval.document_count",
                float(len(docs)),
                kind="histogram",
                mode=mode,
                org_id=org_id or "",
            )
            # Record document quality metrics (relevance scores)
            if docs:
                avg_score = sum(doc.score for doc in docs) / len(docs)
                top_score = docs[0].score if docs else 0.0
                engine.metrics_recorder.record(
                    "rag_control.retrieval.document_score",
                    avg_score,
                    kind="histogram",
                    mode=mode,
                    org_id=org_id or "",
                )
                engine.metrics_recorder.record(
                    "rag_control.retrieval.top_document_score",
                    top_score,
                    kind="histogram",
                    mode=mode,
                    org_id=org_id or "",
                )
            # Record query complexity metric
            engine.metrics_recorder.record(
                "rag_control.query.length_chars",
                float(len(query)),
                kind="histogram",
                mode=mode,
                org_id=org_id or "",
            )
            # Record policy resolution metric
            engine.metrics_recorder.record(
                "rag_control.policy.resolved_by_name",
                1.0,
                kind="counter",
                mode=mode,
                org_id=org_id or "",
                policy_name=policy_name,
            )
            # Record LLM token metrics if available
            if response.usage is not None:
                model_name = response.metadata.model if response.metadata is not None else "unknown"
                prompt_tokens = float(response.usage.prompt_tokens)
                completion_tokens = float(response.usage.completion_tokens)

                engine.metrics_recorder.record(
                    "rag_control.llm.prompt_tokens",
                    prompt_tokens,
                    kind="counter",
                    mode=mode,
                    org_id=org_id or "",
                    model=model_name,
                )
                engine.metrics_recorder.record(
                    "rag_control.llm.completion_tokens",
                    completion_tokens,
                    kind="counter",
                    mode=mode,
                    org_id=org_id or "",
                    model=model_name,
                )
                # Record token efficiency metric
                if prompt_tokens > 0:
                    efficiency_ratio = completion_tokens / prompt_tokens
                    engine.metrics_recorder.record(
                        "rag_control.llm.token_efficiency",
                        efficiency_ratio,
                        kind="histogram",
                        mode=mode,
                        org_id=org_id or "",
                        model=model_name,
                    )
                # Record total tokens
                total_tokens = prompt_tokens + completion_tokens
                engine.metrics_recorder.record(
                    "rag_control.llm.total_tokens",
                    total_tokens,
                    kind="counter",
                    mode=mode,
                    org_id=org_id or "",
                    model=model_name,
                )

            if streaming:
                return StreamResponse(
                    policy_name=policy_name,
                    org_id=org_id,
                    user_id=user_context.user_id,
                    trace_id=trace_id,
                    filter_name=policy.document_policy.filter_name,
                    retrieval_top_k=policy.document_policy.top_k,
                    retrieved_count=len(docs),
                    enforcement_attached=True,
                    response=enforced_response,
                )
            return RunResponse(
                policy_name=policy_name,
                org_id=org_id,
                user_id=user_context.user_id,
                trace_id=trace_id,
                filter_name=policy.document_policy.filter_name,
                retrieval_top_k=policy.document_policy.top_k,
                retrieved_count=len(docs),
                enforcement_passed=True,
                response=enforced_response,
            )
        except Exception as exc:
            # Record request metrics on error
            request_duration_ms = (time.perf_counter() - request_started_at) * 1000
            engine.metrics_recorder.record(
                "rag_control.requests",
                1.0,
                kind="counter",
                mode=mode,
                org_id=org_id or "",
                status="error",
            )
            engine.metrics_recorder.record(
                "rag_control.request.duration_ms",
                request_duration_ms,
                kind="histogram",
                unit="ms",
                mode=mode,
                org_id=org_id or "",
                status="error",
            )
            # Record error categorization metrics
            error_type = exc.__class__.__name__
            engine.metrics_recorder.record(
                "rag_control.errors_by_type",
                1.0,
                kind="counter",
                mode=mode,
                org_id=org_id or "",
                error_type=error_type,
            )
            # Categorize error by source (governance, enforcement, etc.)
            error_category = _categorize_error(error_type)
            engine.metrics_recorder.record(
                "rag_control.errors_by_category",
                1.0,
                kind="counter",
                mode=mode,
                org_id=org_id or "",
                error_category=error_category,
            )
            # Record denied request metrics separately from system errors
            if _is_denied_request(error_type):
                engine.metrics_recorder.record(
                    "rag_control.requests.denied",
                    1.0,
                    kind="counter",
                    mode=mode,
                    org_id=org_id or "",
                    denial_reason=error_category,
                )

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
            span_kind="internal",
            **fields,
        )

    def _run_stage(
        self,
        parent_span: TraceSpan,
        name: str,
        func: Callable[[], T],
        success_fields: Callable[[T], dict[str, Any]] | None = None,
        metrics_labels: dict[str, str] | None = None,
        **fields: Any,
    ) -> T:
        span = self._start_child_span(parent_span, name, **fields)
        started_at = time.perf_counter()
        try:
            result = func()
            stage_latency_ms = (time.perf_counter() - started_at) * 1000
            success_payload = success_fields(result) if success_fields is not None else {}
            span.finish(
                status="ok",
                stage_latency_ms=stage_latency_ms,
                **success_payload,
            )
            if metrics_labels is not None:
                self.metrics_recorder.record(
                    "rag_control.stage.duration_ms",
                    stage_latency_ms,
                    kind="histogram",
                    unit="ms",
                    **{**metrics_labels, "status": "ok"},
                )
            return result
        except Exception as exc:
            stage_latency_ms = (time.perf_counter() - started_at) * 1000
            span.finish(
                status="error",
                error_type=exc.__class__.__name__,
                error_message=str(exc),
                stage_latency_ms=stage_latency_ms,
            )
            if metrics_labels is not None:
                self.metrics_recorder.record(
                    "rag_control.stage.duration_ms",
                    stage_latency_ms,
                    kind="histogram",
                    unit="ms",
                    **{**metrics_labels, "status": "error"},
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


def _categorize_error(error_type: str) -> str:
    """Categorize error types for metrics tracking."""
    if "Governance" in error_type:
        return "governance"
    if "Enforcement" in error_type:
        return "enforcement"
    if "Embedding" in error_type:
        return "embedding"
    if "VectorStore" in error_type or "Retrieval" in error_type:
        return "retrieval"
    if "LLM" in error_type:
        return "llm"
    if "Policy" in error_type:
        return "policy"
    return "other"


def _is_denied_request(error_type: str) -> bool:
    """Check if error represents a denied (rejected) request vs system error."""
    # Denied requests are business rule rejections, not system failures
    return any(keyword in error_type for keyword in {"Governance", "Enforcement", "Policy"})
