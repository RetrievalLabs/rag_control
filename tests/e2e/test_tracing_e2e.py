"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from rag_control.core.engine import RAGControl
from rag_control.exceptions import GovernanceUserContextOrgIDRequiredError
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


class _CapturedSpan:
    def __init__(
        self,
        collector: "_CapturedTracer",
        *,
        name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> None:
        self._collector = collector
        self.span_id = f"span-{len(collector.started_spans) + 1}"
        self.trace_id = trace_id if trace_id is not None else str(uuid4())
        collector.started_spans.append(
            {
                "span_id": self.span_id,
                "trace_id": self.trace_id,
                "parent_span_id": parent_span_id,
                "span_name": name,
            }
        )

    def event(self, event: str, **fields: Any) -> None:
        self._collector.events.append(
            {
                "span_id": self.span_id,
                "trace_id": self.trace_id,
                "event": event,
                **fields,
            }
        )

    def finish(
        self,
        *,
        status: str = "ok",
        error_type: str | None = None,
        error_message: str | None = None,
        **fields: Any,
    ) -> None:
        self._collector.finished_spans.append(
            {
                "span_id": self.span_id,
                "trace_id": self.trace_id,
                "status": status,
                "error_type": error_type,
                "error_message": error_message,
                **fields,
            }
        )


class _CapturedTracer:
    def __init__(self) -> None:
        self.started_spans: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.finished_spans: list[dict[str, Any]] = []

    def start_span(
        self,
        name: str,
        **fields: Any,
    ) -> _CapturedSpan:
        trace_id = fields.pop("trace_id", None)
        parent_span_id = fields.pop("parent_span_id", None)
        span = _CapturedSpan(
            self,
            name=name,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        self.events.append(
            {
                "span_id": span.span_id,
                "trace_id": span.trace_id,
                "event": "span.started",
                "span_name": name,
                **fields,
            }
        )
        return span


def test_rag_control_run_emits_trace_lifecycle_events(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    tracer = _CapturedTracer()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-trace-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-trace-001",
                content="Policy status is approved.",
                score=0.97,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-trace-001",
    )
    llm.enqueue_response(
        content="approved answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-trace-001",
        prompt_tokens=12,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        tracer=tracer,
    )
    user_context = UserContext(
        user_id="u-trace-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    run_response = engine.run("what is policy status?", user_context=user_context)

    span_names = [span["span_name"] for span in tracer.started_spans]
    assert span_names[0] == "rag_control.request.run"
    for stage in (
        "org_lookup",
        "embedding",
        "retrieval",
        "policy.resolve",
        "prompt.build",
        "llm.generate",
        "enforcement",
    ):
        assert f"rag_control.request.run.stage.{stage}" in span_names

    event_names = [event["event"] for event in tracer.events]
    for event in (
        "transition.request.received",
        "transition.org_lookup.started",
        "transition.org_lookup.completed",
        "transition.request.completed",
    ):
        assert event in event_names

    root_finished = next(
        span
        for span in tracer.finished_spans
        if span["span_id"] == tracer.started_spans[0]["span_id"]
    )
    assert root_finished["status"] == "ok"
    assert root_finished["trace_id"] == run_response.trace_id
    assert root_finished["policy_name"] == "default_policy"


def test_rag_control_stream_stage_spans_have_parent_kind_and_latency(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    tracer = _CapturedTracer()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-trace-stream-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-trace-stream-001",
                content="Policy status is approved.",
                score=0.97,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-trace-stream-001",
    )
    llm.enqueue_response(
        content="approved answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-trace-stream-001",
        prompt_tokens=12,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        tracer=tracer,
    )
    user_context = UserContext(
        user_id="u-trace-stream-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    stream_response = engine.stream("what is policy status?", user_context=user_context)
    root_span_id = tracer.started_spans[0]["span_id"]

    span_started_events = [event for event in tracer.events if event["event"] == "span.started"]
    root_started = next(event for event in span_started_events if event["span_id"] == root_span_id)
    assert root_started["span_kind"] == "internal"

    for started_span in tracer.started_spans[1:]:
        assert started_span["parent_span_id"] == root_span_id
        started_event = next(
            event for event in span_started_events if event["span_id"] == started_span["span_id"]
        )
        assert started_event["span_kind"] == "internal"
        finished_span = next(
            span for span in tracer.finished_spans if span["span_id"] == started_span["span_id"]
        )
        assert finished_span["status"] == "ok"
        assert isinstance(finished_span["stage_latency_ms"], float)
        assert finished_span["stage_latency_ms"] >= 0

    assert stream_response.enforcement_attached is True


def test_rag_control_run_marks_failing_stage_with_error_and_latency(
    fake_config: ControlPlaneConfig,
) -> None:
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    tracer = _CapturedTracer()
    query_embedding.fail_next(RuntimeError("embed failed"))

    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        tracer=tracer,
    )
    user_context = UserContext(
        user_id="u-trace-error-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    with pytest.raises(RuntimeError, match="embed failed"):
        engine.run("policy question", user_context=user_context)

    embedding_span_start = next(
        span
        for span in tracer.started_spans
        if span["span_name"] == "rag_control.request.run.stage.embedding"
    )
    embedding_span_finish = next(
        span for span in tracer.finished_spans if span["span_id"] == embedding_span_start["span_id"]
    )
    assert embedding_span_finish["status"] == "error"
    assert embedding_span_finish["error_type"] == "RuntimeError"
    assert embedding_span_finish["error_message"] == "embed failed"
    assert isinstance(embedding_span_finish["stage_latency_ms"], float)
    assert embedding_span_finish["stage_latency_ms"] >= 0

    root_finished = next(
        span
        for span in tracer.finished_spans
        if span["span_id"] == tracer.started_spans[0]["span_id"]
    )
    assert root_finished["status"] == "error"
    assert root_finished["error_type"] == "RuntimeError"


def test_rag_control_run_finishes_error_trace_when_org_id_missing(
    fake_config: ControlPlaneConfig,
) -> None:
    tracer = _CapturedTracer()
    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=FakeQueryEmbedding(model="fake-embedding-v1"),
        vector_store=FakeVectorStore(embedding_model="fake-embedding-v1"),
        config=fake_config,
        tracer=tracer,
    )
    invalid_user_context = UserContext.model_construct(
        user_id="u-trace-2",
        org_id=None,
        attributes={},
    )

    with pytest.raises(GovernanceUserContextOrgIDRequiredError):
        engine.run("policy question", user_context=invalid_user_context)

    finished = next(
        span
        for span in tracer.finished_spans
        if span["span_id"] == tracer.started_spans[0]["span_id"]
    )
    assert finished["status"] == "error"
    assert finished["error_type"] == "GovernanceUserContextOrgIDRequiredError"

    event_names = [event["event"] for event in tracer.events]
    assert "warning.request.denied" in event_names
    assert "error.request.failed" in event_names
