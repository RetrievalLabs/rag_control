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


def test_metrics_e2e_records_document_quality_metrics(
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
        request_id="embed-quality-001",
    )
    # Return documents with different scores
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-quality-001",
                content="Document 1.",
                score=0.95,
                metadata={"source": "kb"},
            ),
            VectorStoreRecord(
                id="doc-quality-002",
                content="Document 2.",
                score=0.85,
                metadata={"source": "kb"},
            ),
            VectorStoreRecord(
                id="doc-quality-003",
                content="Document 3.",
                score=0.75,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-quality-001",
    )
    llm.enqueue_response(
        content="Answer [DOC 1] [DOC 2] [DOC 3]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-quality-001",
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
        user_id="u-quality-1",
        org_id="test_org",
        attributes={},
    )

    engine.run("test query", user_context=user_context)

    # Find document score metrics
    doc_score_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.retrieval.document_score"
    ]
    assert len(doc_score_calls) == 1
    # Average of 0.95, 0.85, 0.75 = 0.85
    assert abs(doc_score_calls[0]["value"] - 0.85) < 0.01
    assert doc_score_calls[0]["kind"] == "histogram"

    # Find top document score metric
    top_score_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.retrieval.top_document_score"
    ]
    assert len(top_score_calls) == 1
    assert top_score_calls[0]["value"] == 0.95


def test_metrics_e2e_records_query_and_policy_metrics(
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
        request_id="embed-query-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-query-001",
                content="Document 1.",
                score=0.95,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-query-001",
    )
    llm.enqueue_response(
        content="Answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-query-001",
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
        user_id="u-query-1",
        org_id="test_org",
        attributes={},
    )

    test_query = "What is the meaning of life?"
    engine.run(test_query, user_context=user_context)

    # Find query length metric
    query_length_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.query.length_chars"
    ]
    assert len(query_length_calls) == 1
    assert query_length_calls[0]["value"] == float(len(test_query))

    # Find policy resolution metric
    policy_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.policy.resolved_by_name"
    ]
    assert len(policy_calls) == 1
    assert policy_calls[0]["policy_name"] == "default_policy"


def test_metrics_e2e_records_llm_efficiency_and_total_tokens(
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
        request_id="embed-eff-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-eff-001",
                content="Document 1.",
                score=0.95,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-eff-001",
    )
    llm.enqueue_response(
        content="Answer [DOC 1]",
        model="gpt-4-turbo",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-eff-001",
        prompt_tokens=100,
        completion_tokens=50,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        metrics_recorder=metrics_recorder,
    )
    user_context = UserContext(
        user_id="u-eff-1",
        org_id="test_org",
        attributes={},
    )

    engine.run("test query", user_context=user_context)

    # Find token efficiency metric
    efficiency_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.llm.token_efficiency"
    ]
    assert len(efficiency_calls) == 1
    assert efficiency_calls[0]["value"] == 0.5  # 50 / 100

    # Find total tokens metric
    total_token_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.llm.total_tokens"
    ]
    assert len(total_token_calls) == 1
    assert total_token_calls[0]["value"] == 150.0  # 100 + 50


def test_metrics_e2e_records_embedding_dimensions(
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
        request_id="embed-dims-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-dims-001",
                content="Document 1.",
                score=0.95,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-dims-001",
    )
    llm.enqueue_response(
        content="Answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-dims-001",
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
        user_id="u-dims-1",
        org_id="test_org",
        attributes={},
    )

    engine.run("test query", user_context=user_context)

    # Find embedding dimensions metric
    dims_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.embedding.dimensions"
    ]
    assert len(dims_calls) == 1
    assert dims_calls[0]["value"] == 3.0  # Embedding has 3 dimensions in test


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

    # Check error categorization metrics
    error_type_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.errors_by_type"
    ]
    assert len(error_type_calls) == 1
    assert error_type_calls[0]["error_type"] == "RuntimeError"

    error_category_calls = [
        c for c in metrics_recorder.calls if c["name"] == "rag_control.errors_by_category"
    ]
    assert len(error_category_calls) == 1
    assert error_category_calls[0]["error_category"] == "other"

    # Denied metric only recorded for governance/enforcement/policy errors
    denied_calls = [c for c in metrics_recorder.calls if c["name"] == "rag_control.requests.denied"]
    assert len(denied_calls) == 0


def test_metrics_e2e_records_denied_requests_on_enforcement_failure(
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
        request_id="embed-denied-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-denied-001",
                content="Document without citation.",  # Missing citation
                score=0.97,
                metadata={"source": "kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="test-index",
        latency_ms=4.0,
        request_id="search-denied-001",
    )
    # Response without required citations will be denied
    llm.enqueue_response(
        content="Answer without citations",  # Will fail enforcement
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-denied-001",
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
        user_id="u-denied-1",
        org_id="test_org",
        attributes={},
    )

    with pytest.raises(Exception):  # EnforcementPolicyViolationError
        engine.run("test query", user_context=user_context)

    # Find denied request metric
    denied_calls = [c for c in metrics_recorder.calls if c["name"] == "rag_control.requests.denied"]
    assert len(denied_calls) == 1
    assert denied_calls[0]["denial_reason"] == "enforcement"
    assert denied_calls[0]["mode"] == "run"
    assert denied_calls[0]["org_id"] == "test_org"
    assert "status" not in denied_calls[0]  # denied_calls don't have status label
