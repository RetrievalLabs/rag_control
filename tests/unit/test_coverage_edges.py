"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from rag_control.adapters.llm import LLM
from rag_control.adapters.query_embedding import QueryEmbedding
from rag_control.adapters.vector_store import VectorStore
from rag_control.core.engine import RAGControl
from rag_control.exceptions.embedding_model import (
    EmbeddingModelMismatchError,
    EmbeddingModelTypeError,
    EmbeddingModelValidationError,
)
from rag_control.exceptions.governance import GovernanceOrgNotFoundError
from rag_control.governance import gov as gov_module
from rag_control.governance.gov import GovernanceRegistry
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.llm import (
    LLMMetadata,
    LLMResponse,
    LLMStreamChunk,
    LLMStreamResponse,
    LLMUsage,
)
from rag_control.models.policy import EnforcementPolicy, GenerationPolicy, LoggingPolicy, Policy
from rag_control.models.deny_rule import DenyRuleCondition, DenyRuleLogicalCondition
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord
from rag_control.observability import audit_logger as audit_logger_module
from rag_control.observability import tracing as tracing_module
from rag_control.policy.policy import PolicyRegistry
from rag_control.prompt.base import PromptBuilder
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


class _LLMSuperCalls(LLM):
    def generate(
        self,
        prompt: Any,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        user_context: Any = None,
    ) -> Any:
        return super().generate(  # type: ignore[safe-super]
            prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            user_context=user_context,
        )

    def stream(
        self,
        prompt: Any,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        user_context: Any = None,
    ) -> Any:
        return super().stream(  # type: ignore[safe-super]
            prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            user_context=user_context,
        )


class _QueryEmbeddingSuperCalls(QueryEmbedding):
    @property
    def embedding_model(self) -> str:
        return super().embedding_model  # type: ignore[safe-super]

    def embed(self, query: str, user_context: Any = None) -> Any:
        return super().embed(query, user_context=user_context)  # type: ignore[safe-super]


class _VectorStoreSuperCalls(VectorStore):
    @property
    def embedding_model(self) -> str:
        return super().embedding_model  # type: ignore[safe-super]

    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        user_context: Any = None,
        filter: Any = None,
    ) -> Any:
        return super().search(  # type: ignore[safe-super]
            embedding,
            top_k=top_k,
            user_context=user_context,
            filter=filter,
        )


class _PromptBuilderSuperCalls(PromptBuilder):
    def build(
        self,
        query: str,
        retrieved_docs: list[VectorStoreRecord],
        policy: Policy | None,
    ) -> list[dict[str, str]]:
        return super().build(query, retrieved_docs, policy)  # type: ignore[safe-super]


def _build_policy_registry_with_default_only() -> PolicyRegistry:
    return PolicyRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                )
            ],
            filters=[],
            orgs=[],
        )
    )


def test_abstract_base_pass_paths_execute() -> None:
    assert _LLMSuperCalls().generate("hi") is None
    assert _LLMSuperCalls().stream("hi") is None
    assert _QueryEmbeddingSuperCalls().embedding_model is None
    assert _QueryEmbeddingSuperCalls().embed("hello") is None
    assert _VectorStoreSuperCalls().embedding_model is None
    assert _VectorStoreSuperCalls().search([0.1]) is None
    assert _PromptBuilderSuperCalls().build("q", [], None) is None


def test_embedding_and_governance_exception_constructors() -> None:
    type_error = EmbeddingModelTypeError("query model")
    assert "query model must be a str" == str(type_error)

    validation_error = EmbeddingModelValidationError("vector model")
    assert "vector model must be non-empty" == str(validation_error)

    mismatch_error = EmbeddingModelMismatchError("a", "b")
    assert "'a' != 'b'" in str(mismatch_error)

    user_context = UserContext(user_id="u", org_id="org-x", attributes={})
    org_not_found = GovernanceOrgNotFoundError(user_context)
    assert org_not_found.user_context == user_context
    assert "governance org not found" in str(org_not_found)


def test_engine_normalize_embedding_model_error_paths(fake_config: ControlPlaneConfig) -> None:
    engine = RAGControl(
        llm=FakeLLM(),
        query_embedding=FakeQueryEmbedding(model="fake-embedding-v1"),
        vector_store=FakeVectorStore(embedding_model="fake-embedding-v1"),
        config=fake_config,
    )

    with pytest.raises(EmbeddingModelTypeError, match="must be a str"):
        engine._normalize_embedding_model(123, "query model")  # type: ignore[arg-type]

    with pytest.raises(EmbeddingModelValidationError, match="must be non-empty"):
        engine._normalize_embedding_model("   ", "query model")


def test_policy_registry_missing_policy_branches_and_helpers() -> None:
    registry = _build_policy_registry_with_default_only()

    response = LLMResponse(
        content="answer",
        usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        metadata=LLMMetadata(model="x", provider="p", latency_ms=1.0),
    )
    stream_response = LLMStreamResponse(
        stream=iter([LLMStreamChunk(delta="chunk")]),
        usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        metadata=LLMMetadata(model="x", provider="p", latency_ms=1.0),
    )

    # policy-not-found branches
    registry.enforce_response(policy_name="missing", response=response, retrieved_docs=[])
    assert (
        registry.enforce_stream_response(
            policy_name="missing",
            response=stream_response,
            retrieved_docs=[],
        )
        is stream_response
    )

    # helper branches
    assert registry._check_max_output_tokens(max_output_tokens=10, completion_tokens=5) == []

    policy = registry.get("default_policy")
    assert policy is not None
    violations = registry._check_response_content(
        policy=policy,
        content="Answer [DOC 99]",
        retrieved_docs=[
            VectorStoreRecord(
                id="doc-1",
                content="c1",
                score=0.8,
                metadata={},
            )
        ],
    )
    assert "invalid citations out of retrieved range" in violations[0]


def test_governance_registry_uncovered_condition_branches(monkeypatch: Any) -> None:
    user_context = UserContext(
        user_id="u-1",
        org_id="test_org",
        attributes={"region": ["us", "eu"], "score": 9, "word": "eu-west"},
    )
    doc = VectorStoreRecord(id="d", content="c", score=0.5, metadata={"score": 9, "region": ["eu"]})

    empty_logical = DenyRuleLogicalCondition.model_construct(all=None, any=None)
    assert GovernanceRegistry._matches_logical_condition(empty_logical, user_context) is False

    assert (
        GovernanceRegistry._matches_condition(
            DenyRuleCondition.model_construct(
                field="score", operator="gt", value=None, source="user"
            ),
            user_context,
        )
        is False
    )
    assert (
        GovernanceRegistry._matches_condition(
            DenyRuleCondition.model_construct(
                field="region",
                operator="intersects",
                value="eu",
                source="user",
            ),
            user_context,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition(
            DenyRuleCondition.model_construct(
                field="score", operator="lt", value=10, source="user"
            ),
            user_context,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition(
            DenyRuleCondition.model_construct(field="score", operator="gt", value=1, source="user"),
            user_context,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition(
            DenyRuleCondition.model_construct(
                field="word",
                operator="intersects",
                value="eu",
                source="user",
            ),
            user_context,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition(
            DenyRuleCondition.model_construct(
                field="score", operator="unknown", value=1, source="user"
            ),
            user_context,
        )
        is False
    )

    monkeypatch.setattr(
        gov_module, "DENY_RULE_NUMERIC_OPERATORS", ("lt", "lte", "gt", "gte", "mystery")
    )
    assert (
        GovernanceRegistry._matches_condition(
            DenyRuleCondition.model_construct(
                field="score", operator="mystery", value=5, source="user"
            ),
            user_context,
        )
        is True
    )

    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.score",
                operator="gt",
                value=None,
                source="documents",
            ),
            doc,
        )
        is False
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.score",
                operator="lt",
                value=10,
                source="documents",
            ),
            doc,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.score",
                operator="lte",
                value=9,
                source="documents",
            ),
            doc,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.score",
                operator="gt",
                value=1,
                source="documents",
            ),
            doc,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.score",
                operator="gte",
                value=9,
                source="documents",
            ),
            doc,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.region",
                operator="intersects",
                value="eu",
                source="documents",
            ),
            doc,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.region",
                operator="intersects",
                value=99,
                source="documents",
            ),
            doc,
        )
        is False
    )
    doc_with_string_region = VectorStoreRecord(
        id="d2",
        content="c2",
        score=0.4,
        metadata={"region": "eu-west-1"},
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.region",
                operator="intersects",
                value="eu",
                source="documents",
            ),
            doc_with_string_region,
        )
        is True
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.score",
                operator="unknown",
                value=1,
                source="documents",
            ),
            doc,
        )
        is False
    )
    assert (
        GovernanceRegistry._matches_condition_for_document(
            DenyRuleCondition.model_construct(
                field="metadata.score",
                operator="mystery",
                value=5,
                source="documents",
            ),
            doc,
        )
        is True
    )


def test_audit_and_tracing_remaining_uncovered_branches(monkeypatch: Any) -> None:
    assert audit_logger_module.should_emit_audit_event("any", "unexpected") is True  # type: ignore[arg-type]

    class _Logger:
        def info(self, event: str, **fields: Any) -> None:
            return None

    span = tracing_module._StructlogTraceSpan(cast(Any, _Logger()), name="s")
    span.finish(status="ok")
    span.finish(status="ok")  # already-finished branch

    class _Span:
        def __init__(self) -> None:
            self.detached = False

        def get_span_context(self) -> Any:
            class _Ctx:
                trace_id = 1
                span_id = 1

            return _Ctx()

        def add_event(self, name: str, attributes: dict[str, Any]) -> None:
            return None

        def set_attributes(self, attributes: dict[str, Any]) -> None:
            return None

        def set_attribute(self, key: str, value: Any) -> None:
            return None

        def set_status(self, status: Any) -> None:
            return None

        def end(self) -> None:
            return None

    otel_context_module = getattr(tracing_module, "otel_context")
    monkeypatch.setattr(
        otel_context_module,
        "detach",
        lambda _: (_ for _ in ()).throw(RuntimeError("detach fail")),
    )
    wrapped = tracing_module._OpenTelemetryTraceSpan(_Span(), detach_token=object())
    wrapped.finish(status="ok")
