"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import Any

import pytest

from rag_control.core.engine import RAGControl
from rag_control.exceptions import (
    EnforcementPolicyViolationError,
    GovernancePolicyDeniedError,
    GovernanceUserContextOrgIDRequiredError,
)
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord
from rag_control.version import __version__
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


class _CapturedAuditLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def log_event(self, event: str, *, level: str = "info", **fields: Any) -> None:
        captured = {"event": event, "level": level}
        captured.update(fields)
        self.events.append(captured)


def test_rag_control_run_emits_audit_lifecycle_events(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    audit_logger = _CapturedAuditLogger()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-audit-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-audit-001",
                content="Policy status is approved.",
                score=0.97,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-audit-001",
    )
    llm.enqueue_response(
        content="approved answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-audit-001",
        prompt_tokens=12,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        audit_logger=audit_logger,
    )
    user_context = UserContext(
        user_id="u-audit-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    engine.run("what is policy status?", user_context=user_context)

    event_names = [event["event"] for event in audit_logger.events]
    assert event_names == [
        "request.received",
        "org.resolved",
        "retrieval.completed",
        "policy.resolved",
        "enforcement.passed",
        "request.completed",
    ]

    request_ids = {event["request_id"] for event in audit_logger.events}
    assert len(request_ids) == 1
    assert next(iter(request_ids))
    for event in audit_logger.events:
        assert event["sdk_name"] == "rag_control"
        assert event["sdk_version"] == __version__
        assert event["company_name"] == "RetrievalLabs"
    retrieval_event = audit_logger.events[2]
    assert retrieval_event["retrieved_doc_ids"] == ["doc-audit-001"]
    assert retrieval_event["retrieved_count"] == 1
    completed_event = audit_logger.events[-1]
    assert completed_event["retrieved_doc_ids"] == ["doc-audit-001"]
    assert completed_event["llm_model"] == "fake-gpt"
    assert completed_event["llm_temperature"] == 0.0
    assert completed_event["prompt_tokens"] == 12
    assert completed_event["completion_tokens"] == 4
    assert completed_event["total_tokens"] == 16


def test_rag_control_run_emits_audit_denied_event_for_missing_org_id(
    fake_config: ControlPlaneConfig,
) -> None:
    audit_logger = _CapturedAuditLogger()
    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=FakeQueryEmbedding(model="fake-embedding-v1"),
        vector_store=FakeVectorStore(embedding_model="fake-embedding-v1"),
        config=fake_config,
        audit_logger=audit_logger,
    )
    invalid_user_context = UserContext.model_construct(
        user_id="u-audit-2",
        org_id=None,
        attributes={},
    )

    with pytest.raises(GovernanceUserContextOrgIDRequiredError):
        engine.run("policy question", user_context=invalid_user_context)

    assert [event["event"] for event in audit_logger.events] == [
        "request.received",
        "request.denied",
    ]
    assert audit_logger.events[-1]["level"] == "warning"
    assert audit_logger.events[-1]["error_type"] == "GovernanceUserContextOrgIDRequiredError"


def test_rag_control_run_minimal_audit_policy_emits_only_minimal_audit_events(
    fake_config: ControlPlaneConfig,
) -> None:
    config = fake_config.model_copy(deep=True)
    config.policies[0].logging.level = "minimal"

    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    audit_logger = _CapturedAuditLogger()

    query_embedding.enqueue_response(
        embedding=[0.15, 0.25, 0.35],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-audit-minimal-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-audit-minimal-001",
                content="Policy status is approved.",
                score=0.97,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-audit-minimal-001",
    )
    llm.enqueue_response(
        content="approved answer [DOC 1]",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-audit-minimal-001",
        prompt_tokens=12,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=config,
        audit_logger=audit_logger,
    )
    user_context = UserContext(
        user_id="u-audit-minimal-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    engine.run("what is policy status?", user_context=user_context)

    assert [event["event"] for event in audit_logger.events] == [
        "request.received",
        "org.resolved",
        "request.completed",
    ]
    completed_event = audit_logger.events[-1]
    assert completed_event["retrieved_doc_ids"] == ["doc-audit-minimal-001"]
    assert completed_event["llm_model"] == "fake-gpt"
    assert completed_event["llm_temperature"] == 0.0
    assert completed_event["prompt_tokens"] == 12
    assert completed_event["completion_tokens"] == 4
    assert completed_event["total_tokens"] == 16


def test_rag_control_stream_emits_llm_details_in_request_completed_audit_event(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    audit_logger = _CapturedAuditLogger()

    query_embedding.enqueue_response(
        embedding=[0.21, 0.31, 0.41],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-audit-stream-001",
    )
    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-audit-stream-001",
                content="Stream policy status is approved.",
                score=0.96,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-audit-stream-001",
    )
    llm.enqueue_response(
        content="approved stream answer [DOC 1]",
        model="fake-stream-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-audit-stream-001",
        prompt_tokens=9,
        completion_tokens=5,
    )

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
        audit_logger=audit_logger,
    )
    user_context = UserContext(
        user_id="u-audit-stream-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    stream_response = engine.stream("what is policy status?", user_context=user_context)
    list(stream_response.response.stream)

    assert [event["event"] for event in audit_logger.events] == [
        "request.received",
        "org.resolved",
        "retrieval.completed",
        "policy.resolved",
        "enforcement.attached",
        "request.completed",
    ]
    completed_event = audit_logger.events[-1]
    assert completed_event["event"] == "request.completed"
    assert completed_event["retrieved_doc_ids"] == ["doc-audit-stream-001"]
    assert completed_event["llm_model"] == "fake-stream-gpt"
    assert completed_event["llm_temperature"] == 0.0
    assert completed_event["prompt_tokens"] == 9
    assert completed_event["completion_tokens"] == 5
    assert completed_event["total_tokens"] == 14


def test_rag_control_run_emits_audit_denied_event_from_governance_registry(
    fake_config: ControlPlaneConfig,
) -> None:
    config = fake_config.model_copy(deep=True)
    config.orgs[0].policy_rules[0].effect = "deny"

    audit_logger = _CapturedAuditLogger()
    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=FakeQueryEmbedding(model="fake-embedding-v1"),
        vector_store=FakeVectorStore(embedding_model="fake-embedding-v1"),
        config=config,
        audit_logger=audit_logger,
    )
    user_context = UserContext(
        user_id="u-audit-deny-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    with pytest.raises(GovernancePolicyDeniedError):
        engine.run("policy question", user_context=user_context)

    assert [event["event"] for event in audit_logger.events] == [
        "request.received",
        "org.resolved",
        "request.denied",
    ]
    denied_event = audit_logger.events[-1]
    assert denied_event["level"] == "warning"
    assert denied_event["rule_name"] == "allow_enterprise"
    assert denied_event["error_type"] == "GovernancePolicyDeniedError"
    assert denied_event["request_id"] == audit_logger.events[0]["request_id"]


def test_rag_control_run_emits_audit_denied_event_from_policy_registry(
    fake_config: ControlPlaneConfig,
) -> None:
    audit_logger = _CapturedAuditLogger()
    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=FakeQueryEmbedding(model="fake-embedding-v1"),
        vector_store=FakeVectorStore(embedding_model="fake-embedding-v1"),
        config=fake_config,
        audit_logger=audit_logger,
    )
    user_context = UserContext(
        user_id="u-audit-policy-deny-1",
        org_id="test_org",
        attributes={"org_tier": "enterprise"},
    )

    with pytest.raises(EnforcementPolicyViolationError):
        engine.run("policy question", user_context=user_context)

    assert audit_logger.events[-1]["event"] == "request.denied"
    assert audit_logger.events[-1]["error_type"] == "EnforcementPolicyViolationError"
    assert audit_logger.events[-1]["request_id"] == audit_logger.events[0]["request_id"]
