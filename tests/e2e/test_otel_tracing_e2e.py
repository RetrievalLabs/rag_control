"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from typing import Any

import pytest
from opentelemetry.trace import StatusCode

from rag_control.core.engine import RAGControl
from rag_control.exceptions import GovernanceUserContextOrgIDRequiredError
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


def _configure_otel_provider() -> tuple[Any, Any, Any]:
    trace = pytest.importorskip("opentelemetry.trace")
    sdk_trace = pytest.importorskip("opentelemetry.sdk.trace")
    sdk_export = pytest.importorskip("opentelemetry.sdk.trace.export")
    in_memory_module = pytest.importorskip("opentelemetry.sdk.trace.export.in_memory_span_exporter")

    provider = trace.get_tracer_provider()
    if not isinstance(provider, sdk_trace.TracerProvider):
        provider = sdk_trace.TracerProvider()
        trace.set_tracer_provider(provider)

    exporter = in_memory_module.InMemorySpanExporter()
    provider.add_span_processor(sdk_export.SimpleSpanProcessor(exporter))
    return trace, provider, exporter


def _build_engine(fake_config: ControlPlaneConfig) -> RAGControl:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-otel-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-otel-001",
                content="Policy status is approved.",
                score=0.97,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-otel-001",
    )
    llm.enqueue_response(
        content="approved answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-otel-001",
        prompt_tokens=12,
    )

    return RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )


def test_rag_control_default_tracer_uses_child_span_when_parent_exists(
    fake_config: ControlPlaneConfig,
) -> None:
    trace, _, exporter = _configure_otel_provider()
    exporter.clear()

    engine = _build_engine(fake_config)
    user_context = UserContext(
        user_id="u-otel-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    parent_tracer = trace.get_tracer("tests.parent")
    with parent_tracer.start_as_current_span("backend.parent") as parent_span:
        run_response = engine.run("what is policy status?", user_context=user_context)
        parent_trace_id = f"{parent_span.get_span_context().trace_id:032x}"

    assert run_response.trace_id == parent_trace_id
    spans = exporter.get_finished_spans()
    request_span = next(span for span in spans if span.name == "rag_control.request.run")
    assert request_span.parent is not None
    assert request_span.parent.span_id == parent_span.get_span_context().span_id


def test_rag_control_default_tracer_uses_root_span_when_no_parent_exists(
    fake_config: ControlPlaneConfig,
) -> None:
    _, _, exporter = _configure_otel_provider()
    exporter.clear()

    engine = _build_engine(fake_config)
    user_context = UserContext(
        user_id="u-otel-2",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    run_response = engine.run("what is policy status?", user_context=user_context)

    spans = exporter.get_finished_spans()
    request_span = next(span for span in spans if span.name == "rag_control.request.run")
    assert request_span.parent is None
    assert run_response.trace_id == f"{request_span.context.trace_id:032x}"
    assert request_span.attributes["enduser.id"] == "u-otel-2"

    llm_span = next(
        span for span in spans if span.name == "rag_control.request.run.stage.llm.generate"
    )
    assert llm_span.attributes["gen_ai.request.model"] == "fake-gpt"
    assert llm_span.attributes["gen_ai.usage.input_tokens"] == 12
    assert llm_span.attributes["gen_ai.usage.output_tokens"] == 4
    assert llm_span.attributes["gen_ai.usage.total_tokens"] == 16


def test_rag_control_stream_records_internal_stage_span_kind_and_latency(
    fake_config: ControlPlaneConfig,
) -> None:
    _, _, exporter = _configure_otel_provider()
    exporter.clear()

    engine = _build_engine(fake_config)
    user_context = UserContext(
        user_id="u-otel-stream-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    stream_response = engine.stream("what is policy status?", user_context=user_context)

    spans = exporter.get_finished_spans()
    request_span = next(span for span in spans if span.name == "rag_control.request.stream")
    assert stream_response.trace_id == f"{request_span.context.trace_id:032x}"
    assert stream_response.enforcement_attached is True
    assert request_span.attributes["span.kind"] == "internal"

    for stage in (
        "org_lookup",
        "embedding",
        "retrieval",
        "policy.resolve",
        "prompt.build",
        "llm.stream",
        "enforcement",
    ):
        stage_span = next(
            span for span in spans if span.name == f"rag_control.request.stream.stage.{stage}"
        )
        assert stage_span.parent is not None
        assert stage_span.parent.span_id == request_span.context.span_id
        assert stage_span.attributes["span.kind"] == "internal"
        assert isinstance(stage_span.attributes["stage_latency_ms"], float)
        assert stage_span.attributes["stage_latency_ms"] >= 0


def test_rag_control_default_tracer_sets_error_semantic_attributes(
    fake_config: ControlPlaneConfig,
) -> None:
    _, _, exporter = _configure_otel_provider()
    exporter.clear()

    engine = _build_engine(fake_config)
    invalid_user_context = UserContext.model_construct(
        user_id="u-otel-error-1",
        org_id=None,
        attributes={},
    )

    with pytest.raises(GovernanceUserContextOrgIDRequiredError):
        engine.run("policy question", user_context=invalid_user_context)

    spans = exporter.get_finished_spans()
    request_span = next(span for span in spans if span.name == "rag_control.request.run")
    assert request_span.status.status_code == StatusCode.ERROR
    for key in ("exception.type", "error.type"):
        assert request_span.attributes[key] == "GovernanceUserContextOrgIDRequiredError"
    for key in ("exception.message", "error.message"):
        assert "org_id" in request_span.attributes[key]
