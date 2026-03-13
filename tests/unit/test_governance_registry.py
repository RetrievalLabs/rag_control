"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import Any, TypedDict

import pytest

from rag_control.exceptions.governance import (
    GovernancePolicyDeniedError,
)
from rag_control.governance.gov import GovernanceRegistry
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.filter import FilterCondition
from rag_control.models.filter import Filter
from rag_control.models.org import OrgConfig
from rag_control.models.policy import (
    EnforcementPolicy,
    GenerationPolicy,
    LoggingPolicy,
    Policy,
)
from rag_control.models.deny_rule import DenyRule, DenyRuleCondition, DenyRuleLogicalCondition
from rag_control.models.policy_rule import (
    PolicyRule,
    PolicyRuleCondition,
    PolicyRuleLogicalCondition,
)
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
                policy_rules=[
                    PolicyRule(
                        name="allow_gold_plan",
                        priority=80,
                        effect="allow",
                        apply_policy="premium_policy",
                        when=PolicyRuleLogicalCondition(
                            any=[
                                PolicyRuleCondition(
                                    field="plan",
                                    operator="equals",
                                    value="gold",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_session_exists",
                        priority=85,
                        effect="allow",
                        apply_policy="research_policy",
                        when=PolicyRuleLogicalCondition(
                            any=[
                                PolicyRuleCondition(
                                    field="session_id",
                                    operator="exists",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="deny_banned_user",
                        priority=100,
                        effect="deny",
                        when=PolicyRuleLogicalCondition(
                            any=[
                                PolicyRuleCondition(
                                    field="user_status",
                                    operator="equals",
                                    value="banned",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_analyst_low_risk",
                        priority=90,
                        effect="allow",
                        apply_policy="research_policy",
                        when=PolicyRuleLogicalCondition(
                            all=[
                                PolicyRuleCondition(
                                    field="role",
                                    operator="equals",
                                    value="analyst",
                                ),
                                PolicyRuleCondition(
                                    field="risk_score",
                                    operator="lte",
                                    value=50,
                                ),
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_high_trust",
                        priority=70,
                        effect="allow",
                        apply_policy="premium_policy",
                        when=PolicyRuleLogicalCondition(
                            any=[
                                PolicyRuleCondition(
                                    field="trust_score",
                                    operator="gte",
                                    value=90,
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_department_via_attributes_path",
                        priority=65,
                        effect="allow",
                        apply_policy="research_policy",
                        when=PolicyRuleLogicalCondition(
                            any=[
                                PolicyRuleCondition(
                                    field="attributes.department",
                                    operator="equals",
                                    value="finance",
                                )
                            ]
                        ),
                    ),
                    PolicyRule(
                        name="allow_eu_default",
                        priority=60,
                        effect="allow",
                        apply_policy="default_policy",
                        when=PolicyRuleLogicalCondition(
                            any=[
                                PolicyRuleCondition(
                                    field="region",
                                    operator="intersects",
                                    value="eu",
                                )
                            ]
                        ),
                    ),
                ],
                deny_rules=[],
            )
        ],
    )


def test_governance_registry_sorts_policy_rules_by_priority_descending() -> None:
    registry = GovernanceRegistry(_build_governance_config())
    org = registry.get_org("test_org")

    assert org is not None
    priorities = [rule.priority for rule in org.policy_rules]
    assert priorities == [100, 90, 85, 80, 70, 65, 60]


def test_governance_registry_sorts_deny_rules_by_priority_descending() -> None:
    """Test that deny_rules are sorted by priority in descending order."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="test_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_priority_50",
                            priority=50,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="status",
                                        operator="equals",
                                        value="pending",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_priority_100",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="status",
                                        operator="equals",
                                        value="banned",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_priority_75",
                            priority=75,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="status",
                                        operator="equals",
                                        value="suspended",
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

    org = registry.get_org("test_org")
    assert org is not None
    priorities = [rule.priority for rule in org.deny_rules]
    # Should be sorted in descending order
    assert priorities == [100, 75, 50]
    rule_names = [rule.name for rule in org.deny_rules]
    assert rule_names == ["deny_priority_100", "deny_priority_75", "deny_priority_50"]


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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="org_id",
                                        operator="equals",
                                        value="special_org",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                    ],
                    deny_rules=[],
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
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
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="region",
                                        operator="intersects",
                                        value="eu",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                    ],
                    deny_rules=[],
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
                            when=PolicyRuleLogicalCondition(
                                all=[
                                    PolicyRuleCondition(
                                        field="department",
                                        operator="equals",
                                        value="finance",
                                        source="user",
                                    )
                                ],
                                any=[
                                    PolicyRuleCondition(
                                        field="region",
                                        operator="equals",
                                        value="eu",
                                        source="user",
                                    )
                                ],
                            ),
                        )
                    ],
                    deny_rules=[],
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


def test_governance_registry_resolve_deny_with_deny_rules() -> None:
    """Test resolve_deny() method with deny rules matching user context."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="deny_test_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_suspicious_users",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="risk_level",
                                        operator="equals",
                                        value="critical",
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_from_blocked_regions",
                            priority=90,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="region",
                                        operator="equals",
                                        value="blocked_zone",
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

    # User matching deny rule should raise GovernancePolicyDeniedError
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(
            UserContext(
                user_id="u-critical",
                org_id="deny_test_org",
                attributes={"risk_level": "critical"},
            )
        )
    assert exc_info.value.rule_name == "deny_suspicious_users"

    # User not matching any deny rule should pass
    registry.resolve_deny(
        UserContext(
            user_id="u-safe",
            org_id="deny_test_org",
            attributes={"risk_level": "low"},
        )
    )


def test_governance_registry_resolve_deny_with_document_source_conditions() -> None:
    """Test resolve_deny() with document source conditions."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="doc_test_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_if_any_doc_has_pii_tag",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="metadata.tags",
                                        operator="intersects",
                                        value="pii",
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_if_all_docs_sensitive",
                            priority=90,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="metadata.classification",
                                        operator="equals",
                                        value="secret",
                                        source="documents",
                                        document_match="all",
                                    )
                                ]
                            ),
                        ),
                    ],
                )
            ],
        )
    )

    user = UserContext(user_id="u-1", org_id="doc_test_org", attributes={})
    docs_with_pii = [
        VectorStoreRecord(
            id="doc1",
            content="content",
            score=0.9,
            metadata={"tags": ["pii", "sensitive"]},
        )
    ]

    # Should deny when any doc has PII tag
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(user, source_documents=docs_with_pii)
    assert exc_info.value.rule_name == "deny_if_any_doc_has_pii_tag"

    # Should allow when no docs have PII tag
    docs_without_pii = [
        VectorStoreRecord(
            id="doc1",
            content="content",
            score=0.9,
            metadata={"tags": ["public", "general"]},
        )
    ]
    registry.resolve_deny(user, source_documents=docs_without_pii)

    # Should deny when all docs are secret
    all_secret_docs = [
        VectorStoreRecord(
            id="doc1",
            content="content",
            score=0.9,
            metadata={"classification": "secret"},
        ),
        VectorStoreRecord(
            id="doc2",
            content="content",
            score=0.8,
            metadata={"classification": "secret"},
        ),
    ]
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(user, source_documents=all_secret_docs)
    assert exc_info.value.rule_name == "deny_if_all_docs_sensitive"

    # Should allow when not all docs are secret
    mixed_docs = [
        VectorStoreRecord(
            id="doc1",
            content="content",
            score=0.9,
            metadata={"classification": "secret"},
        ),
        VectorStoreRecord(
            id="doc2",
            content="content",
            score=0.8,
            metadata={"classification": "public"},
        ),
    ]
    registry.resolve_deny(user, source_documents=mixed_docs)


def test_governance_registry_with_audit_logging_context() -> None:
    """Test resolve_deny() and resolve_policy() with audit logging."""
    logged_events = []

    class MockAuditLogger:
        def log_event(self, event: str, *, level: str = "info", **fields: Any) -> None:
            logged_events.append({"event": event, "level": level, **fields})

    class MockAuditContext:
        def __init__(self) -> None:
            self.logger = MockAuditLogger()

        def log_event(self, event: str, **kwargs: Any) -> None:
            self.logger.log_event(event, **kwargs)

    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="audit_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="deny_rule_audit",
                            priority=100,
                            effect="deny",
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="status",
                                        operator="equals",
                                        value="blocked",
                                        source="user",
                                    )
                                ]
                            ),
                        )
                    ],
                    deny_rules=[
                        DenyRule(
                            name="deny_high_risk",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="risk",
                                        operator="equals",
                                        value="high",
                                        source="user",
                                    )
                                ]
                            ),
                        )
                    ],
                )
            ],
        )
    )

    # Test resolve_deny() with audit logging
    logged_events.clear()
    audit_context = MockAuditContext()
    user_high_risk = UserContext(
        user_id="u-risk", org_id="audit_org", attributes={"risk": "high"}
    )

    with pytest.raises(GovernancePolicyDeniedError):
        registry.resolve_deny(user_high_risk, audit_context=audit_context)

    assert len(logged_events) == 1
    event = logged_events[0]
    assert event["event"] == "request.denied"
    assert event["rule_name"] == "deny_high_risk"
    assert event["error_type"] == "GovernancePolicyDeniedError"
    assert "governance policy denied" in event["error_message"]

    # Test resolve_policy() with deny effect and audit logging
    logged_events.clear()
    user_blocked = UserContext(
        user_id="u-blocked", org_id="audit_org", attributes={"status": "blocked"}
    )

    with pytest.raises(GovernancePolicyDeniedError):
        registry.resolve_policy(user_blocked, audit_context=audit_context)

    assert len(logged_events) == 1
    event = logged_events[0]
    assert event["event"] == "request.denied"
    assert event["rule_name"] == "deny_rule_audit"
    assert event["error_type"] == "GovernancePolicyDeniedError"


def test_governance_registry_deny_logical_condition_all_and_any() -> None:
    """Test _matches_deny_logical_condition() with all and any combinations."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="logical_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_all_and_any",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                all=[
                                    DenyRuleCondition(
                                        field="department",
                                        operator="equals",
                                        value="finance",
                                        source="user",
                                    )
                                ],
                                any=[
                                    DenyRuleCondition(
                                        field="risk",
                                        operator="equals",
                                        value="high",
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

    # all=True, any=True -> deny
    with pytest.raises(GovernancePolicyDeniedError):
        registry.resolve_deny(
            UserContext(
                user_id="u-deny",
                org_id="logical_org",
                attributes={"department": "finance", "risk": "high"},
            )
        )

    # all=True, any=False -> allow
    registry.resolve_deny(
        UserContext(
            user_id="u-allow-1",
            org_id="logical_org",
            attributes={"department": "finance", "risk": "low"},
        )
    )

    # all=False, any=True -> allow
    registry.resolve_deny(
        UserContext(
            user_id="u-allow-2",
            org_id="logical_org",
            attributes={"department": "hr", "risk": "high"},
        )
    )

    # all=False, any=False -> allow
    registry.resolve_deny(
        UserContext(
            user_id="u-allow-3",
            org_id="logical_org",
            attributes={"department": "hr", "risk": "low"},
        )
    )


def test_governance_registry_empty_deny_rules_list() -> None:
    """Test organization with empty deny rules list resolves correctly."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="test_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[],  # Empty deny rules
                )
            ],
        )
    )

    # Should allow when deny_rules is empty
    registry.resolve_deny(
        UserContext(
            user_id="u-1",
            org_id="test_org",
            attributes={"tier": "standard"},
        )
    )


def test_governance_registry_deny_condition_numeric_operators_all_branches() -> None:
    """Test all numeric operators (lt, lte, gt, gte) in deny conditions."""
    # Each operator tested with separate registry to avoid priority conflicts

    # Test lt operator
    registry_lt = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="numeric_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_score_lt_20",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="lt",
                                        value=20,
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
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry_lt.resolve_deny(
            UserContext(user_id="u-1", org_id="numeric_org", attributes={"score": 10})
        )
    assert exc_info.value.rule_name == "deny_score_lt_20"

    # Test lte operator
    registry_lte = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="numeric_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_score_lte_30",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="lte",
                                        value=30,
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
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry_lte.resolve_deny(
            UserContext(user_id="u-2", org_id="numeric_org", attributes={"score": 30})
        )
    assert exc_info.value.rule_name == "deny_score_lte_30"

    # Test gt operator
    registry_gt = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="numeric_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_score_gt_80",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="gt",
                                        value=80,
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
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry_gt.resolve_deny(
            UserContext(user_id="u-3", org_id="numeric_org", attributes={"score": 85})
        )
    assert exc_info.value.rule_name == "deny_score_gt_80"

    # Test gte operator
    registry_gte = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="numeric_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_score_gte_90",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="gte",
                                        value=90,
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
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry_gte.resolve_deny(
            UserContext(user_id="u-4", org_id="numeric_org", attributes={"score": 95})
        )
    assert exc_info.value.rule_name == "deny_score_gte_90"


def test_governance_registry_policy_condition_numeric_operators_all_branches() -> None:
    """Test all numeric operators (lt, lte, gt, gte) in policy conditions."""
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
                    name="premium_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="standard_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
                Policy(
                    name="vip_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="numeric_policy_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_score_lt_30",
                            priority=40,
                            effect="allow",
                            apply_policy="standard_policy",
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="score",
                                        operator="lt",
                                        value=30,
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_score_lte_50",
                            priority=30,
                            effect="allow",
                            apply_policy="premium_policy",
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="score",
                                        operator="lte",
                                        value=50,
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_score_gt_70",
                            priority=20,
                            effect="allow",
                            apply_policy="vip_policy",
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="score",
                                        operator="gt",
                                        value=70,
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                        PolicyRule(
                            name="allow_score_gte_85",
                            priority=10,
                            effect="allow",
                            apply_policy="vip_policy",
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="score",
                                        operator="gte",
                                        value=85,
                                        source="user",
                                    )
                                ]
                            ),
                        ),
                    ],
                    deny_rules=[],
                )
            ],
        )
    )

    # Test lt operator
    assert (
        registry.resolve_policy(
            UserContext(user_id="u-1", org_id="numeric_policy_org", attributes={"score": 20})
        )
        == "standard_policy"
    )

    # Test lte operator
    assert (
        registry.resolve_policy(
            UserContext(user_id="u-2", org_id="numeric_policy_org", attributes={"score": 50})
        )
        == "premium_policy"
    )

    # Test gt operator
    assert (
        registry.resolve_policy(
            UserContext(user_id="u-3", org_id="numeric_policy_org", attributes={"score": 75})
        )
        == "vip_policy"
    )

    # Test gte operator
    assert (
        registry.resolve_policy(
            UserContext(user_id="u-4", org_id="numeric_policy_org", attributes={"score": 90})
        )
        == "vip_policy"
    )


def test_governance_registry_document_condition_all_operators() -> None:
    """Test all operators in document conditions."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="doc_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_if_doc_score_lt_threshold",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="lt",
                                        value=0.5,
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_if_doc_score_lte",
                            priority=90,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="lte",
                                        value=0.5,
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_if_doc_score_gt",
                            priority=80,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="gt",
                                        value=0.9,
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_if_doc_score_gte",
                            priority=70,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="gte",
                                        value=0.9,
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_if_doc_classification_equals",
                            priority=60,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="metadata.classification",
                                        operator="equals",
                                        value="confidential",
                                        source="documents",
                                        document_match="any",
                                    )
                                ]
                            ),
                        ),
                        DenyRule(
                            name="deny_if_doc_has_tags",
                            priority=50,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="metadata.tags",
                                        operator="intersects",
                                        value="restricted",
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

    user = UserContext(user_id="u-1", org_id="doc_org", attributes={})

    # Test lt operator on document score
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(
            user,
            source_documents=[
                VectorStoreRecord(id="d1", content="c", score=0.3, metadata={})
            ],
        )
    assert exc_info.value.rule_name == "deny_if_doc_score_lt_threshold"

    # Test lte operator on document score
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(
            user,
            source_documents=[
                VectorStoreRecord(id="d1", content="c", score=0.5, metadata={})
            ],
        )
    assert exc_info.value.rule_name == "deny_if_doc_score_lte"

    # Test gt operator on document score
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(
            user,
            source_documents=[
                VectorStoreRecord(id="d1", content="c", score=0.95, metadata={})
            ],
        )
    assert exc_info.value.rule_name == "deny_if_doc_score_gt"

    # Test gte operator on document score
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(
            user,
            source_documents=[
                VectorStoreRecord(id="d1", content="c", score=0.9, metadata={})
            ],
        )
    assert exc_info.value.rule_name == "deny_if_doc_score_gte"

    # Test equals operator on document metadata
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(
            user,
            source_documents=[
                VectorStoreRecord(
                    id="d1",
                    content="c",
                    score=0.7,
                    metadata={"classification": "confidential"},
                )
            ],
        )
    assert exc_info.value.rule_name == "deny_if_doc_classification_equals"

    # Test intersects operator on document metadata list
    with pytest.raises(GovernancePolicyDeniedError) as exc_info:
        registry.resolve_deny(
            user,
            source_documents=[
                VectorStoreRecord(
                    id="d1",
                    content="c",
                    score=0.7,
                    metadata={"tags": ["restricted", "internal"]},
                )
            ],
        )
    assert exc_info.value.rule_name == "deny_if_doc_has_tags"


def test_governance_registry_document_condition_exists_operator() -> None:
    """Test exists operator in document conditions."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="doc_exists_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_if_doc_has_classification",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
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

    user = UserContext(user_id="u-1", org_id="doc_exists_org", attributes={})

    # Should deny when doc has classification field
    with pytest.raises(GovernancePolicyDeniedError):
        registry.resolve_deny(
            user,
            source_documents=[
                VectorStoreRecord(
                    id="d1",
                    content="c",
                    score=0.7,
                    metadata={"classification": "public"},
                )
            ],
        )

    # Should allow when doc doesn't have classification field
    registry.resolve_deny(
        user,
        source_documents=[VectorStoreRecord(id="d1", content="c", score=0.7, metadata={})],
    )


def test_governance_registry_condition_type_mismatch_edge_cases() -> None:
    """Test edge cases where condition values don't match expected types."""
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
                    name="premium_policy",
                    generation=GenerationPolicy(),
                    logging=LoggingPolicy(),
                    enforcement=EnforcementPolicy(),
                ),
            ],
            filters=[],
            orgs=[
                OrgConfig(
                    org_id="type_mismatch_org",
                    default_policy="default_policy",
                    policy_rules=[
                        PolicyRule(
                            name="allow_numeric_comparison",
                            priority=100,
                            effect="allow",
                            apply_policy="premium_policy",
                            when=PolicyRuleLogicalCondition(
                                any=[
                                    PolicyRuleCondition(
                                        field="score",
                                        operator="gte",
                                        value=80,
                                        source="user",
                                    )
                                ]
                            ),
                        )
                    ],
                    deny_rules=[],
                )
            ],
        )
    )

    # String value with numeric operator should fall back to default
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-1",
                org_id="type_mismatch_org",
                attributes={"score": "very high"},  # String instead of number
            )
        )
        == "default_policy"
    )

    # List value with numeric operator should fall back to default
    assert (
        registry.resolve_policy(
            UserContext(
                user_id="u-2",
                org_id="type_mismatch_org",
                attributes={"score": [80, 90]},  # List instead of number
            )
        )
        == "default_policy"
    )


def test_governance_registry_deny_condition_type_mismatch_edge_cases() -> None:
    """Test edge cases in deny conditions with type mismatches."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="deny_type_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_high_score",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="score",
                                        operator="gte",
                                        value=80,
                                        source="user",
                                    )
                                ]
                            ),
                        )
                    ],
                )
            ],
        )
    )

    # String value with numeric operator should not match
    registry.resolve_deny(
        UserContext(
            user_id="u-1",
            org_id="deny_type_org",
            attributes={"score": "very high"},  # String instead of number
        )
    )

    # List value with numeric operator should not match
    registry.resolve_deny(
        UserContext(
            user_id="u-2",
            org_id="deny_type_org",
            attributes={"score": [80, 90]},  # List instead of number
        )
    )


def test_governance_registry_document_condition_with_empty_source_documents() -> None:
    """Test document conditions when source_documents list is empty."""
    registry = GovernanceRegistry(
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
            orgs=[
                OrgConfig(
                    org_id="empty_docs_org",
                    default_policy="default_policy",
                    policy_rules=[],
                    deny_rules=[
                        DenyRule(
                            name="deny_with_docs",
                            priority=100,
                            when=DenyRuleLogicalCondition(
                                any=[
                                    DenyRuleCondition(
                                        field="metadata.score",
                                        operator="gt",
                                        value=0.5,
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

    user = UserContext(user_id="u-1", org_id="empty_docs_org", attributes={})

    # Should allow when source_documents is empty (no docs to match condition)
    registry.resolve_deny(user, source_documents=[])

    # Should also allow when source_documents is None (handled as empty list)
    registry.resolve_deny(user, source_documents=None)


def test_governance_registry_unknown_numeric_operator_fallback(monkeypatch: Any) -> None:
    """Test fallback behavior when numeric operator isn't explicitly handled."""
    from rag_control.models import policy_rule, deny_rule

    user = UserContext(user_id="u-1", org_id="test_org", attributes={"score": 85})
    doc = VectorStoreRecord(id="d1", content="c", score=0.9, metadata={})

    # Test policy condition with unknown numeric operator
    monkeypatch.setattr(
        policy_rule,
        "POLICY_RULE_NUMERIC_OPERATORS",
        ("lt", "lte", "gt", "gte", "unknown_numeric")
    )
    condition = PolicyRuleCondition.model_construct(
        field="score", operator="unknown_numeric", value=85
    )
    result = GovernanceRegistry._matches_policy_condition(condition, user)
    assert result is False  # Should return False for unknown operator

    # Test deny condition with unknown numeric operator
    monkeypatch.setattr(
        deny_rule,
        "DENY_RULE_NUMERIC_OPERATORS",
        ("lt", "lte", "gt", "gte", "mystery_op")
    )
    deny_condition = DenyRuleCondition.model_construct(
        field="score", operator="mystery_op", value=85, source="user"
    )
    result = GovernanceRegistry._matches_deny_condition(deny_condition, user)
    assert result is False

    # Test document condition with unknown operator
    doc_condition = DenyRuleCondition.model_construct(
        field="score", operator="unknown_op", value=0.5, source="documents"
    )
    result = GovernanceRegistry._matches_condition_for_document(doc_condition, doc)
    assert result is False


def test_governance_registry_intersects_operator_with_wrong_types() -> None:
    """Test intersects operator when actual_value is not list/string."""
    user = UserContext(user_id="u-1", org_id="test_org", attributes={"tags": 123})  # int instead of list/string

    # Policy condition with intersects on non-list/string value
    condition = PolicyRuleCondition.model_construct(
        field="tags", operator="intersects", value="tag"
    )
    result = GovernanceRegistry._matches_policy_condition(condition, user)
    assert result is False

    # Deny condition with intersects on non-list/string value
    deny_condition = DenyRuleCondition.model_construct(
        field="tags", operator="intersects", value="tag", source="user"
    )
    result = GovernanceRegistry._matches_deny_condition(deny_condition, user)
    assert result is False

    # Document condition with intersects on non-list/string metadata value
    doc = VectorStoreRecord(
        id="d1", content="c", score=0.9, metadata={"tags": 123}  # int instead of list/string
    )
    doc_condition = DenyRuleCondition.model_construct(
        field="metadata.tags", operator="intersects", value="tag", source="documents"
    )
    result = GovernanceRegistry._matches_condition_for_document(doc_condition, doc)
    assert result is False


def test_governance_registry_intersects_with_list_value_not_found() -> None:
    """Test intersects operator when value is not in the list."""
    # Policy condition with intersects on list where value not found
    condition = PolicyRuleCondition.model_construct(
        field="tags", operator="intersects", value="missing_tag"
    )
    user = UserContext(user_id="u-1", org_id="test_org", attributes={"tags": ["tag1", "tag2"]})
    result = GovernanceRegistry._matches_policy_condition(condition, user)
    assert result is False  # "missing_tag" not in ["tag1", "tag2"]

    # Deny condition with intersects on list where value not found
    deny_condition = DenyRuleCondition.model_construct(
        field="tags", operator="intersects", value="missing_tag", source="user"
    )
    result = GovernanceRegistry._matches_deny_condition(deny_condition, user)
    assert result is False

    # Document condition with intersects on list where value not found
    doc = VectorStoreRecord(
        id="d1", content="c", score=0.9, metadata={"tags": ["doc1", "doc2"]}
    )
    doc_condition = DenyRuleCondition.model_construct(
        field="metadata.tags", operator="intersects", value="doc3", source="documents"
    )
    result = GovernanceRegistry._matches_condition_for_document(doc_condition, doc)
    assert result is False


def test_governance_registry_edge_cases_with_model_construct() -> None:
    """Test edge cases using model_construct to bypass validation constraints."""
    user = UserContext(user_id="u-1", org_id="test_org", attributes={"score": 85})

    # Test _matches_policy_logical_condition with both all and any None (defensive code path)
    logical_condition = PolicyRuleLogicalCondition.model_construct(all=None, any=None)
    result = GovernanceRegistry._matches_policy_logical_condition(logical_condition, user)
    assert result is False

    # Test _matches_policy_condition with expected_value=None and equals operator
    condition = PolicyRuleCondition.model_construct(
        field="score", operator="equals", value=None
    )
    result = GovernanceRegistry._matches_policy_condition(condition, user)
    assert result is False

    # Test _matches_policy_condition with None expected value and numeric operator
    condition_numeric = PolicyRuleCondition.model_construct(
        field="score", operator="gt", value=None
    )
    result = GovernanceRegistry._matches_policy_condition(condition_numeric, user)
    assert result is False

    # Test _matches_deny_logical_condition with both all and any None
    deny_logical = DenyRuleLogicalCondition.model_construct(all=None, any=None)
    result = GovernanceRegistry._matches_deny_logical_condition(deny_logical, user)
    assert result is False

    # Test _matches_deny_condition with expected_value=None
    deny_condition = DenyRuleCondition.model_construct(
        field="score", operator="equals", value=None, source="user"
    )
    result = GovernanceRegistry._matches_deny_condition(deny_condition, user)
    assert result is False

    # Test _matches_deny_condition with None expected value and numeric operator
    deny_numeric = DenyRuleCondition.model_construct(
        field="score", operator="gt", value=None, source="user"
    )
    result = GovernanceRegistry._matches_deny_condition(deny_numeric, user)
    assert result is False

    # Test _matches_condition_for_document with expected_value=None
    doc = VectorStoreRecord(id="d1", content="c", score=0.9, metadata={})
    doc_condition = DenyRuleCondition.model_construct(
        field="score", operator="equals", value=None, source="documents"
    )
    result = GovernanceRegistry._matches_condition_for_document(doc_condition, doc)
    assert result is False

    # Test _matches_condition_for_document with None value and numeric operator
    doc_numeric = DenyRuleCondition.model_construct(
        field="score", operator="gt", value=None, source="documents"
    )
    result = GovernanceRegistry._matches_condition_for_document(doc_numeric, doc)
    assert result is False


