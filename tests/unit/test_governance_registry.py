"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import TypedDict

import pytest

from rag_control.exceptions.governance import (
    GovernancePolicyDeniedError,
)
from rag_control.governance.gov import GovernanceRegistry
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.filter import Condition as FilterCondition
from rag_control.models.filter import Filter
from rag_control.models.org import DocumentPolicy, OrgConfig
from rag_control.models.policy import (
    EnforcementPolicy,
    GenerationPolicy,
    LoggingPolicy,
    Policy,
)
from rag_control.models.access_rule import Condition, LogicalCondition, PolicyRule
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord


class _ResolvePolicyCase(TypedDict):
    name: str
    user_context: UserContext
    expected_policy: str | None
    expected_exception: type[Exception] | None
    expected_rule_name: str | None


def _build_governance_config() -> ControlPlaneConfig:
    return ControlPlaneConfig(
        policies=[
            Policy(
                name="default_policy",
                generation=GenerationPolicy(),
                logging=LoggingPolicy(),
                enforcement=EnforcementPolicy(),
            ),
            Policy(
                name="research_policy",
                generation=GenerationPolicy(reasoning_level="full", fallback="soft"),
                logging=LoggingPolicy(level="full"),
                enforcement=EnforcementPolicy(block_on_missing_citations=False),
            ),
            Policy(
                name="premium_policy",
                generation=GenerationPolicy(reasoning_level="limited"),
                logging=LoggingPolicy(level="full"),
                enforcement=EnforcementPolicy(max_output_tokens=2048),
            ),
        ],
        filters=[
            Filter(
                name="default_filter",
                condition=FilterCondition(
                    field="org_tier",
                    operator="equals",
                    value="enterprise",
                    source="user",
                ),
            )
        ],
        orgs=[
            OrgConfig(
                org_id="test_org",
                default_policy="default_policy",
                document_policy=DocumentPolicy(filter_name="default_filter"),
                policy_rules=[
                    PolicyRule(
                        name="allow_gold_plan",
                        priority=80,
                        effect="allow",
                        apply_policy="premium_policy",
                        when=LogicalCondition(
                            any=[
                                Condition(
                                    field="plan",
                                    operator="equals",
                                    value="gold",
                                    source="user",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_session_exists",
                        priority=85,
                        effect="allow",
                        apply_policy="research_policy",
                        when=LogicalCondition(
                            any=[
                                Condition(
                                    field="session_id",
                                    operator="exists",
                                    source="user",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="deny_banned_user",
                        priority=100,
                        effect="deny",
                        when=LogicalCondition(
                            any=[
                                Condition(
                                    field="user_status",
                                    operator="equals",
                                    value="banned",
                                    source="user",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_analyst_low_risk",
                        priority=90,
                        effect="allow",
                        apply_policy="research_policy",
                        when=LogicalCondition(
                            all=[
                                Condition(
                                    field="role",
                                    operator="equals",
                                    value="analyst",
                                    source="user",
                                ),
                                Condition(
                                    field="risk_score",
                                    operator="lte",
                                    value=50,
                                    source="user",
                                ),
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_high_trust",
                        priority=70,
                        effect="allow",
                        apply_policy="premium_policy",
                        when=LogicalCondition(
                            any=[
                                Condition(
                                    field="trust_score",
                                    operator="gte",
                                    value=90,
                                    source="user",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_department_via_attributes_path",
                        priority=65,
                        effect="allow",
                        apply_policy="research_policy",
                        when=LogicalCondition(
                            any=[
                                Condition(
                                    field="attributes.department",
                                    operator="equals",
                                    value="finance",
                                    source="user",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_eu_default",
                        priority=60,
                        effect="allow",
                        when=LogicalCondition(
                            any=[
                                Condition(
                                    field="region",
                                    operator="intersects",
                                    value="eu",
                                    source="user",
                                )
                            ]
                        ),
                    ),
                ],
            )
        ],
    )


def test_governance_registry_sorts_policy_rules_by_priority_descending() -> None:
    registry = GovernanceRegistry(_build_governance_config())
    org = registry.get_org("test_org")

    assert org is not None
    priorities = [rule.priority for rule in org.policy_rules]
    assert priorities == [100, 90, 85, 80, 70, 65, 60]


def test_governance_registry_resolve_policy_with_multiple_conditions() -> None:
    registry = GovernanceRegistry(_build_governance_config())

    test_cases: list[_ResolvePolicyCase] = [
        {
            "name": "deny_rule_highest_priority",
            "user_context": UserContext(
                user_id="u-1",
                org_id="test_org",
                attributes={"user_status": "banned", "plan": "gold", "trust_score": 99},
            ),
            "expected_policy": None,
            "expected_exception": GovernancePolicyDeniedError,
            "expected_rule_name": "deny_banned_user",
        },
        {
            "name": "allow_analyst_low_risk_all_conditions_match",
            "user_context": UserContext(
                user_id="u-2",
                org_id="test_org",
                attributes={"role": "analyst", "risk_score": 40},
            ),
            "expected_policy": "research_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "missing_key_in_all_conditions_falls_back_to_default",
            "user_context": UserContext(
                user_id="u-3",
                org_id="test_org",
                attributes={"role": "analyst"},
            ),
            "expected_policy": "default_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "gold_plan_any_condition_match",
            "user_context": UserContext(
                user_id="u-4",
                org_id="test_org",
                attributes={"plan": "gold"},
            ),
            "expected_policy": "premium_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "exists_operator_matches_when_key_present",
            "user_context": UserContext(
                user_id="u-4b",
                org_id="test_org",
                attributes={"session_id": "sess-123"},
            ),
            "expected_policy": "research_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "numeric_gte_rule_match",
            "user_context": UserContext(
                user_id="u-5",
                org_id="test_org",
                attributes={"trust_score": 95},
            ),
            "expected_policy": "premium_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "numeric_operator_with_wrong_context_type_falls_back_to_default",
            "user_context": UserContext(
                user_id="u-5b",
                org_id="test_org",
                attributes={"trust_score": "high"},
            ),
            "expected_policy": "default_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "attributes_dot_path_matches_user_attribute",
            "user_context": UserContext(
                user_id="u-5c",
                org_id="test_org",
                attributes={"department": "finance"},
            ),
            "expected_policy": "research_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "exists_operator_false_when_key_missing",
            "user_context": UserContext(
                user_id="u-6b",
                org_id="test_org",
                attributes={"region": "ap-south-1"},
            ),
            "expected_policy": "default_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "intersects_string_rule_uses_default_policy",
            "user_context": UserContext(
                user_id="u-6",
                org_id="test_org",
                attributes={"region": "eu-west-1"},
            ),
            "expected_policy": "default_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "intersects_with_wrong_context_type_falls_back_to_default",
            "user_context": UserContext(
                user_id="u-6c",
                org_id="test_org",
                attributes={"region": 123},
            ),
            "expected_policy": "default_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
        {
            "name": "no_rule_match_uses_default_policy",
            "user_context": UserContext(
                user_id="u-7",
                org_id="test_org",
                attributes={"plan": "silver", "risk_score": 80},
            ),
            "expected_policy": "default_policy",
            "expected_exception": None,
            "expected_rule_name": None,
        },
    ]

    for case in test_cases:
        expected_exception = case["expected_exception"]
        if expected_exception is None:
            policy_name = registry.resolve_policy(case["user_context"])
            assert policy_name == case["expected_policy"], case["name"]
            continue

        with pytest.raises(expected_exception) as exc_info:
            registry.resolve_policy(case["user_context"])

        error = exc_info.value
        if isinstance(error, GovernancePolicyDeniedError):
            assert error.rule_name == case["expected_rule_name"], case["name"]
            assert error.user_context == case["user_context"], case["name"]


def test_governance_registry_resolve_policy_with_source_document_match_modes() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="any_doc_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="all_docs_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="doc_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_all_docs_public",
                            priority=90,
                            effect="allow",
                            apply_policy="all_docs_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="metadata.classification",
                                        operator="equals",
                                        value="public",
                                        source="documents",
                                        document_match="all",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_any_doc_public",
                            priority=80,
                            effect="allow",
                            apply_policy="any_doc_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="metadata.classification",
                                        operator="equals",
                                        value="public",
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                    ],
                )
            ],
        )
    )
    user_context = UserContext(user_id="u-docs", org_id="doc_org", attributes={})

    all_public_docs = [
        VectorStoreRecord(
            id="doc-1",
            content="alpha",
            score=0.95,
            metadata={"classification": "public"},
        ),
        VectorStoreRecord(
            id="doc-2",
            content="beta",
            score=0.91,
            metadata={"classification": "public"},
        ),
    ]
    mixed_docs = [
        VectorStoreRecord(
            id="doc-3",
            content="gamma",
            score=0.93,
            metadata={"classification": "public"},
        ),
        VectorStoreRecord(
            id="doc-4",
            content="delta",
            score=0.89,
            metadata={"classification": "internal"},
        ),
    ]
    no_public_docs = [
        VectorStoreRecord(
            id="doc-5",
            content="epsilon",
            score=0.85,
            metadata={"classification": "internal"},
        )
    ]

    assert (
        registry.resolve_policy(user_context, source_documents=all_public_docs) == "all_docs_policy"
    )
    assert registry.resolve_policy(user_context, source_documents=mixed_docs) == "any_doc_policy"
    assert (
        registry.resolve_policy(user_context, source_documents=no_public_docs) == "default_policy"
    )
    assert registry.resolve_policy(user_context, source_documents=[]) == "default_policy"


def test_governance_registry_resolve_policy_with_user_context_root_and_extra_fields() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="org_scope_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="user_id_scope_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="profile_scope_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="department_scope_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="region_status_scope_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="region_status_top_scope_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="special_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_region_status_top_match",
                            priority=60,
                            effect="allow",
                            apply_policy="region_status_top_scope_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="region.status.top",
                                        operator="equals",
                                        value="green",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_region_status_match",
                            priority=50,
                            effect="allow",
                            apply_policy="region_status_scope_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="region.status",
                                        operator="equals",
                                        value="active",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_department_match",
                            priority=40,
                            effect="allow",
                            apply_policy="department_scope_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="department",
                                        operator="equals",
                                        value="finance",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_user_id_match",
                            priority=30,
                            effect="allow",
                            apply_policy="user_id_scope_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="user_id",
                                        operator="equals",
                                        value="vip-user",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_nested_extra_field_match",
                            priority=20,
                            effect="allow",
                            apply_policy="profile_scope_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="profile.department",
                                        operator="equals",
                                        value="security",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_org_id_match",
                            priority=10,
                            effect="allow",
                            apply_policy="org_scope_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="org_id",
                                        operator="equals",
                                        value="special_org",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                    ],
                )
            ],
        )
    )

    assert (
        registry.resolve_policy(
            UserContext(user_id="u-1", org_id="special_org", attributes={"role": "analyst"})
        )
        == "org_scope_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(user_id="vip-user", org_id="special_org", attributes={"role": "analyst"})
        )
        == "user_id_scope_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext.model_validate(
                {
                    "user_id": "u-3",
                    "org_id": "special_org",
                    "attributes": {"role": "analyst"},
                    "profile": {"department": "security"},
                }
            )
        )
        == "profile_scope_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-4",
                org_id="special_org",
                attributes={"department": "finance"},
            )
        )
        == "department_scope_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-5",
                org_id="special_org",
                attributes={"region": {"status": "active"}},
            )
        )
        == "region_status_scope_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-6",
                org_id="special_org",
                attributes={"region": {"status": {"top": "green"}}},
            )
        )
        == "region_status_top_scope_policy"
    )


def test_governance_registry_resolve_policy_with_nested_document_paths() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="doc_status_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="doc_status_top_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="doc_nested_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_doc_region_status_top",
                            priority=20,
                            effect="allow",
                            apply_policy="doc_status_top_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="metadata.region.status.top",
                                        operator="equals",
                                        value="green",
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_doc_region_status",
                            priority=10,
                            effect="allow",
                            apply_policy="doc_status_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="metadata.region.status",
                                        operator="equals",
                                        value="active",
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                    ],
                )
            ],
        )
    )
    user_context = UserContext(user_id="u-doc-nested", org_id="doc_nested_org", attributes={})

    top_nested_docs = [
        VectorStoreRecord(
            id="doc-n1",
            content="nested-top",
            score=0.91,
            metadata={"region": {"status": {"top": "green"}}},
        )
    ]
    mid_nested_docs = [
        VectorStoreRecord(
            id="doc-n2",
            content="nested-mid",
            score=0.87,
            metadata={"region": {"status": "active"}},
        )
    ]
    no_match_docs = [
        VectorStoreRecord(
            id="doc-n3",
            content="nested-none",
            score=0.73,
            metadata={"region": {"status": "inactive"}},
        )
    ]

    assert (
        registry.resolve_policy(user_context, source_documents=top_nested_docs)
        == "doc_status_top_policy"
    )
    assert (
        registry.resolve_policy(user_context, source_documents=mid_nested_docs)
        == "doc_status_policy"
    )
    assert registry.resolve_policy(user_context, source_documents=no_match_docs) == "default_policy"


def test_governance_registry_document_missing_field_falls_back_to_default() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="doc_exists_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="doc_missing_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_when_classification_exists_on_any_doc",
                            priority=10,
                            effect="allow",
                            apply_policy="doc_exists_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="metadata.classification",
                                        operator="exists",
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        )
                    ],
                )
            ],
        )
    )
    user_context = UserContext(user_id="u-doc-missing", org_id="doc_missing_org", attributes={})

    docs_with_missing_field = [
        VectorStoreRecord(
            id="doc-m1",
            content="missing-classification",
            score=0.74,
            metadata={"source": "kb"},
        )
    ]

    assert (
        registry.resolve_policy(user_context, source_documents=docs_with_missing_field)
        == "default_policy"
    )


def test_governance_registry_document_wrong_type_falls_back_to_default() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="doc_numeric_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="doc_intersects_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="doc_type_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_numeric_doc_score",
                            priority=20,
                            effect="allow",
                            apply_policy="doc_numeric_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="metadata.risk_score",
                                        operator="gte",
                                        value=80,
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_doc_region_intersects",
                            priority=10,
                            effect="allow",
                            apply_policy="doc_intersects_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="metadata.region",
                                        operator="intersects",
                                        value="eu",
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                    ],
                )
            ],
        )
    )
    user_context = UserContext(user_id="u-doc-type", org_id="doc_type_org", attributes={})

    docs_with_wrong_numeric_type = [
        VectorStoreRecord(
            id="doc-t1",
            content="risk-as-string",
            score=0.8,
            metadata={"risk_score": "high"},
        )
    ]
    docs_with_wrong_intersects_type = [
        VectorStoreRecord(
            id="doc-t2",
            content="region-as-number",
            score=0.81,
            metadata={"region": 123},
        )
    ]

    assert (
        registry.resolve_policy(user_context, source_documents=docs_with_wrong_numeric_type)
        == "default_policy"
    )
    assert (
        registry.resolve_policy(user_context, source_documents=docs_with_wrong_intersects_type)
        == "default_policy"
    )


def test_governance_registry_resolve_policy_with_mixed_user_and_document_conditions() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="mixed_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="mixed_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_analyst_with_public_docs",
                            priority=10,
                            effect="allow",
                            apply_policy="mixed_policy",
                            when=LogicalCondition(
                                all=[
                                    Condition(
                                        field="user_role",
                                        operator="equals",
                                        value="analyst",
                                        source="user",
                                    ),
                                    Condition(
                                        field="metadata.classification",
                                        operator="equals",
                                        value="public",
                                        source="documents",
                                        document_match="any",
                                    ),
                                ]
                            ),
                        )
                    ],
                )
            ],
        )
    )

    matching_docs = [
        VectorStoreRecord(
            id="mix-doc-1",
            content="public-doc",
            score=0.9,
            metadata={"classification": "public"},
        )
    ]
    non_matching_docs = [
        VectorStoreRecord(
            id="mix-doc-2",
            content="internal-doc",
            score=0.7,
            metadata={"classification": "internal"},
        )
    ]

    assert (
        registry.resolve_policy(
            UserContext(
                user_id="m-1",
                org_id="mixed_org",
                attributes={"user_role": "analyst"},
            ),
            source_documents=matching_docs,
        )
        == "mixed_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="m-2",
                org_id="mixed_org",
                attributes={"user_role": "viewer"},
            ),
            source_documents=matching_docs,
        )
        == "default_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="m-3",
                org_id="mixed_org",
                attributes={"user_role": "analyst"},
            ),
            source_documents=non_matching_docs,
        )
        == "default_policy"
    )


def test_governance_registry_user_context_missing_and_wrong_types_fall_back_to_default() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="profile_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="risk_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="region_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="user_type_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_profile_department_exists",
                            priority=30,
                            effect="allow",
                            apply_policy="profile_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="profile.department",
                                        operator="exists",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_risk_score_gte_80",
                            priority=20,
                            effect="allow",
                            apply_policy="risk_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="risk.score",
                                        operator="gte",
                                        value=80,
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_region_intersects_eu",
                            priority=10,
                            effect="allow",
                            apply_policy="region_policy",
                            when=LogicalCondition(
                                any=[
                                    Condition(
                                        field="region",
                                        operator="intersects",
                                        value="eu",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                    ],
                )
            ],
        )
    )

    assert (
        registry.resolve_policy(
            UserContext.model_validate(
                {
                    "user_id": "u-pass",
                    "org_id": "user_type_org",
                    "attributes": {"risk": {"score": 90}},
                    "profile": {"department": "security"},
                }
            )
        )
        == "profile_policy"
    )

    assert (
        registry.resolve_policy(
            UserContext(user_id="u-missing-1", org_id="user_type_org", attributes={})
        )
        == "default_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext.model_validate(
                {
                    "user_id": "u-missing-2",
                    "org_id": "user_type_org",
                    "attributes": {},
                    "profile": {},
                }
            )
        )
        == "default_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext.model_validate(
                {
                    "user_id": "u-missing-3",
                    "org_id": "user_type_org",
                    "attributes": {},
                    "profile": "security",
                }
            )
        )
        == "default_policy"
    )

    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-type-1",
                org_id="user_type_org",
                attributes={"risk": {"score": "high"}},
            )
        )
        == "default_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-type-2",
                org_id="user_type_org",
                attributes={"risk": {"score": {"value": 95}}},
            )
        )
        == "default_policy"
    )
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-type-3",
                org_id="user_type_org",
                attributes={"region": {"name": "eu"}},
            )
        )
        == "default_policy"
    )


def test_governance_registry_logical_condition_requires_all_and_any_when_both_present() -> None:
    registry = GovernanceRegistry(
        ControlPlaneConfig(
            policies=[
                Policy(
                    name="default_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="combined_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="logical_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_all_and_any_rule",
                            priority=10,
                            effect="allow",
                            apply_policy="combined_policy",
                            when=LogicalCondition(
                                all=[
                                    Condition(
                                        field="department",
                                        operator="equals",
                                        value="finance",
                                        source="user",
                                    )
                                ],
                                any=[
                                    Condition(
                                        field="region",
                                        operator="equals",
                                        value="eu",
                                        source="user",
                                    )
                                ],
                            ),
                        )
                    ],
                )
            ],
        )
    )

    # all=True, any=True -> match
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="l-1",
                org_id="logical_org",
                attributes={"department": "finance", "region": "eu"},
            )
        )
        == "combined_policy"
    )
    # all=True, any=False -> no match
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="l-2",
                org_id="logical_org",
                attributes={"department": "finance", "region": "us"},
            )
        )
        == "default_policy"
    )
    # all=False, any=True -> no match
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="l-3",
                org_id="logical_org",
                attributes={"department": "legal", "region": "eu"},
            )
        )
        == "default_policy"
    )
