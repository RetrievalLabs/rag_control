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
from rag_control.models.filter import FilterCondition
from rag_control.models.filter import Filter
from rag_control.models.org import OrgConfig
from rag_control.models.document import DocumentPolicy
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
