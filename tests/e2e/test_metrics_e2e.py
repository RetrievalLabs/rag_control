"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from typing import Any

import pytest

from rag_control.core.engine import RAGControl
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


class _CapturedMetricsRecorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def record(
        self,
        name: str,
        value: float,
        *,
        kind: str = "counter",
        unit: str = "",
        **labels: str,
    ) -> None:
        self.calls.append(
            {
                "name": name,
                "value": value,
                "kind": kind,
                "unit": unit,
                **labels,
            }
        )


def test_metrics_e2e_run_emits_request_count_and_duration(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    metrics_recorder = _CapturedMetricsRecorder()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-metrics-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-metrics-001",
                content="Sample content.",
                score=0.97,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-metrics-001",
    )
    llm.enqueue_response(
        content="Sample answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-metrics-001",
        prompt_tokens=10,
        completion_tokens=5,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        metrics_recorder=metrics_recorder,
    )
    user_context = UserContext(
        user_id="u-metrics-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    engine.run("test query", user_context=user_context)

    # Find request counter
    request_count_calls = [c for c in metrics_recorder.calls if c["name"] == "rag_control.requests"]
    assert len(request_count_calls) == 1
    assert request_count_calls[0]["value"] == 1.0
    assert request_count_calls[0]["kind"] == "counter"
    assert request_count_calls[0]["mode"] == "run"
    assert request_count_calls[0]["org_id"] == "test_org"
    assert request_count_calls[0]["status"] == "ok"

    # Find request duration
    request_duration_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.request.duration_ms"
    ]
    assert len(request_duration_calls) == 1
    assert request_duration_calls[0]["kind"] == "histogram"
    assert request_duration_calls[0]["unit"] == "ms"
    assert request_duration_calls[0]["value"] > 0
    assert request_duration_calls[0]["mode"] == "run"
    assert request_duration_calls[0]["org_id"] == "test_org"
    assert request_duration_calls[0]["status"] == "ok"


def test_metrics_e2e_stream_emits_request_metrics(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    metrics_recorder = _CapturedMetricsRecorder()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-metrics-stream-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-metrics-stream-001",
                content="Sample stream content.",
                score=0.97,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-metrics-stream-001",
    )
    llm.enqueue_response(
        content="Hello world [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-metrics-stream-001",
        prompt_tokens=10,
        completion_tokens=2,
        stream_chunks=("Hello", " ", "world [DOC 1]"),
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        metrics_recorder=metrics_recorder,
    )
    user_context = UserContext(
        user_id="u-metrics-stream-1",
        org_id="test_org",
        attributes={},
    )

    response = engine.stream("test query", user_context=user_context)
    # Consume stream
    for _ in response.response:
        pass

    # Find request counter with stream mode
    request_count_calls = [c for c in metrics_recorder.calls if c["name"] == "rag_control.requests"]
    assert len(request_count_calls) == 1
    assert request_count_calls[0]["mode"] == "stream"
    assert request_count_calls[0]["org_id"] == "test_org"
    assert request_count_calls[0]["status"] == "ok"


def test_metrics_e2e_records_stage_duration_for_each_stage(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    metrics_recorder = _CapturedMetricsRecorder()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-metrics-stage-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-metrics-stage-001",
                content="Sample content.",
                score=0.97,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-metrics-stage-001",
    )
    llm.enqueue_response(
        content="Sample answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-metrics-stage-001",
        prompt_tokens=10,
        completion_tokens=5,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        metrics_recorder=metrics_recorder,
    )
    user_context = UserContext(
        user_id="u-metrics-stage-1",
        org_id="test_org",
        attributes={},
    )

    engine.run("test query", user_context=user_context)

    # Find stage duration metrics
    stage_duration_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.stage.duration_ms"
    ]

    # Should have metrics for all stages (with status="ok")
    stage_names = {c["stage"] for c in stage_duration_calls if c["status"] == "ok"}
    expected_stages = {
        "org_lookup",
        "embedding",
        "retrieval",
        "policy.resolve",
        "prompt.build",
        "llm.generate",
        "enforcement",
    }
    assert stage_names == expected_stages

    # Each stage metric should have the right properties
    for call in stage_duration_calls:
        assert call["kind"] == "histogram"
        assert call["unit"] == "ms"
        assert call["value"] > 0
        assert call["mode"] == "run"
        assert call["org_id"] == "test_org"


def test_metrics_e2e_records_llm_token_metrics(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    metrics_recorder = _CapturedMetricsRecorder()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-metrics-tokens-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-metrics-tokens-001",
                content="Sample content.",
                score=0.97,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-metrics-tokens-001",
    )
    llm.enqueue_response(
        content="Sample answer [DOC 1]",
        model="gpt-4-turbo",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-metrics-tokens-001",
        prompt_tokens=123,
        completion_tokens=45,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        metrics_recorder=metrics_recorder,
    )
    user_context = UserContext(
        user_id="u-metrics-tokens-1",
        org_id="test_org",
        attributes={},
    )

    engine.run("test query", user_context=user_context)

    # Find prompt token metrics
    prompt_token_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.llm.prompt_tokens"
    ]
    assert len(prompt_token_calls) == 1
    assert prompt_token_calls[0]["value"] == 123.0
    assert prompt_token_calls[0]["kind"] == "counter"
    assert prompt_token_calls[0]["model"] == "gpt-4-turbo"

    # Find completion token metrics
    completion_token_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.llm.completion_tokens"
    ]
    assert len(completion_token_calls) == 1
    assert completion_token_calls[0]["value"] == 45.0
    assert completion_token_calls[0]["kind"] == "counter"
    assert completion_token_calls[0]["model"] == "gpt-4-turbo"


def test_metrics_e2e_records_retrieval_document_count(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    metrics_recorder = _CapturedMetricsRecorder()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-metrics-docs-001",
    )
    # Return multiple documents
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id=f"doc-metrics-docs-{i}",
                content=f"Document {i} content.",
                score=0.97 - (i * 0.05),
                metadata={"source": "kb"},
            )
            for i in range(5)
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-metrics-docs-001",
    )
    llm.enqueue_response(
        content="Sample answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-metrics-docs-001",
        prompt_tokens=10,
        completion_tokens=5,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        metrics_recorder=metrics_recorder,
    )
    user_context = UserContext(
        user_id="u-metrics-docs-1",
        org_id="test_org",
        attributes={},
    )

    engine.run("test query", user_context=user_context)

    # Find retrieval document count metrics
    doc_count_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.retrieval.document_count"
    ]
    assert len(doc_count_calls) == 1
    assert doc_count_calls[0]["value"] == 5.0
    assert doc_count_calls[0]["kind"] == "histogram"


def test_metrics_e2e_error_path_emits_error_status(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    metrics_recorder = _CapturedMetricsRecorder()

    # Set up initial responses
    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-metrics-error-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-metrics-error-001",
                content="Sample content.",
                score=0.97,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-metrics-error-001",
    )
    # Make LLM fail on next call
    llm.fail_next(RuntimeError("Simulated LLM failure"))

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        metrics_recorder=metrics_recorder,
    )
    user_context = UserContext(
        user_id="u-metrics-error-1",
        org_id="test_org",
        attributes={},
    )

    with pytest.raises(RuntimeError):
        engine.run("test query", user_context=user_context)

    # Find request counter with error status
    request_count_calls = [c for c in metrics_recorder.calls if c["name"] == "rag_control.requests"]
    assert len(request_count_calls) == 1
    assert request_count_calls[0]["status"] == "error"

    # Find request duration with error status
    request_duration_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.request.duration_ms"
    ]
    assert len(request_duration_calls) == 1
    assert request_duration_calls[0]["status"] == "error"

    # Stage metrics should have error status for failed stage
    stage_duration_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.stage.duration_ms"
    ]
    # Find the llm.generate stage (which should fail)
    failed_llm_stage_calls = [
        c for c in stage_duration_calls if c["stage"] == "llm.generate" and c["status"] == "error"
    ]
    assert len(failed_llm_stage_calls) == 1
