"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

import pytest

from rag_control.core.engine import RAGControl
from rag_control.exceptions import (
    EnforcementPolicyViolationError,
    GovernanceRegistryOrgNotFoundError,
    GovernanceUserContextOrgIDRequiredError,
)
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


def test_rag_control_run_returns_llm_response_with_retrieval_context(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-001",
    )

    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-001",
                content="Policy status is approved.",
                score=0.97,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-001",
    )

    llm.enqueue_response(
        content="approved answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-001",
        prompt_tokens=12,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )
    user_context = UserContext(
        user_id="u-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )
    llm_response = engine.run("what is policy status?", user_context=user_context)

    assert llm_response.policy_name == "default_policy"
    assert llm_response.org_id == "test_org"
    assert llm_response.user_id == "u-1"
    assert llm_response.filter_name == "default_filter"
    assert llm_response.retrieval_top_k == 5
    assert llm_response.retrieved_count == 1
    assert llm_response.enforcement_passed is True
    assert llm_response.response.content == "approved answer [DOC 1]"
    assert llm_response.response.metadata.model == "fake-gpt"
    assert llm_response.response.metadata.provider == "fake-provider"
    assert llm_response.response.metadata.latency_ms == 10.0
    assert llm_response.response.metadata.request_id == "req-001"
    assert llm_response.response.usage.total_tokens >= llm_response.response.usage.prompt_tokens
    assert llm_response.response.usage.total_tokens >= llm_response.response.usage.completion_tokens

    assert isinstance(llm.prompts[0], list)
    assert llm.prompts[0][-1]["role"] == "user"
    assert "what is policy status?" in llm.prompts[0][-1]["content"]
    assert query_embedding.queries == ["what is policy status?"]
    assert vector_store.embeddings == [[0.11, 0.22, 0.33]]
    assert vector_store.top_ks == [5]
    assert query_embedding.user_contexts == [user_context]
    assert vector_store.user_contexts == [user_context]
    assert llm.generate_user_contexts == [user_context]
    assert llm.generate_temperatures == [0.0]
    assert len(vector_store.filters) == 1
    assert vector_store.filters[0] is not None
    assert vector_store.filters[0].name == "default_filter"
    assert vector_store.search_calls == 1
    assert llm.generate_calls == 1
    assert llm.stream_calls == 0
    assert query_embedding.embed_calls == 1


def test_rag_control_stream_returns_llm_stream_response_with_retrieval_context(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")

    query_embedding.enqueue_response(
        embedding=[0.31, 0.42, 0.53],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-002",
    )

    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-002",
                content="Policy owner is ops.",
                score=0.93,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-002",
    )

    llm.enqueue_response(
        content="streamed answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-002",
        prompt_tokens=11,
        stream_chunks=("streamed ", "answer ", "[DOC 1]"),
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )
    user_context = UserContext(
        user_id="u-2",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )
    llm_stream_response = engine.stream("who owns policy?", user_context=user_context)

    streamed_text = "".join(chunk.delta for chunk in llm_stream_response.response.stream)

    assert llm_stream_response.policy_name == "default_policy"
    assert llm_stream_response.org_id == "test_org"
    assert llm_stream_response.user_id == "u-2"
    assert llm_stream_response.filter_name == "default_filter"
    assert llm_stream_response.retrieval_top_k == 5
    assert llm_stream_response.retrieved_count == 1
    assert llm_stream_response.enforcement_passed is True
    assert streamed_text == "streamed answer [DOC 1]"
    assert llm_stream_response.response.metadata is not None
    assert llm_stream_response.response.metadata.model == "fake-gpt"
    assert llm_stream_response.response.metadata.provider == "fake-provider"
    assert llm_stream_response.response.metadata.latency_ms == 10.0
    assert llm_stream_response.response.metadata.request_id == "req-002"
    assert llm_stream_response.response.usage is not None
    assert (
        llm_stream_response.response.usage.total_tokens
        >= llm_stream_response.response.usage.prompt_tokens
    )
    assert (
        llm_stream_response.response.usage.total_tokens
        >= llm_stream_response.response.usage.completion_tokens
    )

    assert isinstance(llm.prompts[0], list)
    assert llm.prompts[0][-1]["role"] == "user"
    assert "who owns policy?" in llm.prompts[0][-1]["content"]
    assert query_embedding.queries == ["who owns policy?"]
    assert vector_store.embeddings == [[0.31, 0.42, 0.53]]
    assert vector_store.top_ks == [5]
    assert query_embedding.user_contexts == [user_context]
    assert vector_store.user_contexts == [user_context]
    assert llm.stream_user_contexts == [user_context]
    assert llm.stream_temperatures == [0.0]
    assert len(vector_store.filters) == 1
    assert vector_store.filters[0] is not None
    assert vector_store.filters[0].name == "default_filter"
    assert vector_store.search_calls == 1
    assert llm.generate_calls == 0
    assert llm.stream_calls == 1
    assert query_embedding.embed_calls == 1


def test_rag_control_run_raises_when_user_context_org_id_is_missing(
    fake_config: ControlPlaneConfig,
) -> None:
    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=FakeQueryEmbedding(model="fake-embedding-v1"),
        vector_store=FakeVectorStore(embedding_model="fake-embedding-v1"),
        config=fake_config,
    )
    # Bypass pydantic validation to exercise runtime guard.
    invalid_user_context = UserContext.model_construct(user_id="u-3", org_id=None, attributes={})

    with pytest.raises(
        GovernanceUserContextOrgIDRequiredError,
        match="org_id is required in user_context",
    ):
        engine.run("policy question", user_context=invalid_user_context)


def test_rag_control_run_raises_when_org_not_found_in_governance_registry(
    fake_config: ControlPlaneConfig,
) -> None:
    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=FakeQueryEmbedding(model="fake-embedding-v1"),
        vector_store=FakeVectorStore(embedding_model="fake-embedding-v1"),
        config=fake_config,
    )
    user_context = UserContext(user_id="u-4", org_id="missing_org", attributes={})

    with pytest.raises(
        GovernanceRegistryOrgNotFoundError,
        match="org_id 'missing_org' not found in governance registry",
    ):
        engine.run("policy question", user_context=user_context)


def test_rag_control_run_enforcement_blocks_missing_citations(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.21, 0.22, 0.23],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-004",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-010",
                content="Policy text from KB.",
                score=0.99,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-004",
    )
    llm.enqueue_response(
        content="answer without citations",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-004",
        prompt_tokens=10,
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )
    user_context = UserContext(
        user_id="u-5",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="missing citations while generation.require_citations",
    ):
        engine.run("policy question", user_context=user_context)


def test_rag_control_stream_enforcement_blocks_missing_citations(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.41, 0.42, 0.43],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-005",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-020",
                content="Policy stream text from KB.",
                score=0.99,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-005",
    )
    llm.enqueue_response(
        content="stream without citations",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-005",
        prompt_tokens=10,
        stream_chunks=("stream ", "without ", "citations"),
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )
    user_context = UserContext(
        user_id="u-6",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )
    response = engine.stream("policy stream question", user_context=user_context)

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="missing citations while generation.require_citations",
    ):
        _ = "".join(chunk.delta for chunk in response.response.stream)


def test_rag_control_run_enforcement_blocks_max_output_tokens(
    fake_config: ControlPlaneConfig,
) -> None:
    config = fake_config.model_copy(deep=True)
    config.policies[0].enforcement.max_output_tokens = 3

    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.51, 0.52, 0.53],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-006",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-030",
                content="Policy token check document.",
                score=0.99,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-006",
    )
    llm.enqueue_response(
        content="this answer is too long [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-006",
        prompt_tokens=10,
        completion_tokens=6,
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=config,
    )
    user_context = UserContext(
        user_id="u-7",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="completion tokens exceed enforcement.max_output_tokens",
    ):
        engine.run("policy token question", user_context=user_context)


def test_rag_control_stream_enforcement_blocks_max_output_tokens(
    fake_config: ControlPlaneConfig,
) -> None:
    config = fake_config.model_copy(deep=True)
    config.policies[0].enforcement.max_output_tokens = 3

    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.61, 0.62, 0.63],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-007",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-040",
                content="Policy token stream document.",
                score=0.99,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-007",
    )
    llm.enqueue_response(
        content="stream too long [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-007",
        prompt_tokens=10,
        completion_tokens=6,
        stream_chunks=("stream ", "too ", "long ", "[DOC 1]"),
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=config,
    )
    user_context = UserContext(
        user_id="u-8",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )
    response = engine.stream("policy token stream question", user_context=user_context)

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="completion tokens exceed enforcement.max_output_tokens",
    ):
        _ = "".join(chunk.delta for chunk in response.response.stream)


def test_rag_control_run_enforcement_blocks_non_strict_fallback_when_no_docs(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.71, 0.72, 0.73],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-008",
    )
    vector_store.enqueue_response(
        records=[],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-008",
    )
    llm.enqueue_response(
        content="best effort answer without strict fallback",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-008",
        prompt_tokens=8,
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )
    user_context = UserContext(
        user_id="u-9",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="response must use strict fallback when no documents are retrieved",
    ):
        engine.run("no docs question", user_context=user_context)


def test_rag_control_stream_enforcement_blocks_non_strict_fallback_when_no_docs(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.81, 0.82, 0.83],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-009",
    )
    vector_store.enqueue_response(
        records=[],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-009",
    )
    llm.enqueue_response(
        content="streamed best effort answer",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-009",
        prompt_tokens=8,
        stream_chunks=("streamed ", "best ", "effort ", "answer"),
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )
    user_context = UserContext(
        user_id="u-10",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )
    response = engine.stream("no docs stream question", user_context=user_context)

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="response must use strict fallback when no documents are retrieved",
    ):
        _ = "".join(chunk.delta for chunk in response.response.stream)


def test_rag_control_run_enforcement_blocks_external_knowledge_without_citations(
    fake_config: ControlPlaneConfig,
) -> None:
    config = fake_config.model_copy(deep=True)
    config.policies[0].generation.require_citations = False

    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.91, 0.92, 0.93],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-010",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-050",
                content="Trusted context exists.",
                score=0.99,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-010",
    )
    llm.enqueue_response(
        content="uncited answer despite available context",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-010",
        prompt_tokens=8,
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=config,
    )
    user_context = UserContext(
        user_id="u-11",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="response may rely on external knowledge: citations are required",
    ):
        engine.run("external knowledge check", user_context=user_context)


def test_rag_control_stream_enforcement_blocks_external_knowledge_without_citations(
    fake_config: ControlPlaneConfig,
) -> None:
    config = fake_config.model_copy(deep=True)
    config.policies[0].generation.require_citations = False

    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    query_embedding.enqueue_response(
        embedding=[0.94, 0.95, 0.96],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-011",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-060",
                content="Trusted context exists for stream.",
                score=0.99,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-011",
    )
    llm.enqueue_response(
        content="uncited streamed answer",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-011",
        prompt_tokens=8,
        stream_chunks=("uncited ", "streamed ", "answer"),
    )
    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=config,
    )
    user_context = UserContext(
        user_id="u-12",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )
    response = engine.stream("external knowledge stream check", user_context=user_context)

    with pytest.raises(
        EnforcementPolicyViolationError,
        match="response may rely on external knowledge: citations are required",
    ):
        _ = "".join(chunk.delta for chunk in response.response.stream)
