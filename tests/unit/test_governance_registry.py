"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import TypedDict

import pytest

from rag_control.exceptions import (
    GovernanceOrgNotFoundError,
    GovernancePolicyDeniedError,
)
from rag_control.governance.gov import GovernanceRegistry
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.filter import Condition as FilterCondition
from rag_control.models.filter import Filter
from rag_control.models.org import OrgConfig
from rag_control.models.policy import (
    EnforcementPolicy,
    GenerationPolicy,
    LoggingPolicy,
    Policy,
)
from rag_control.models.rule import Condition, LogicalCondition, PolicyRule
from rag_control.models.user_context import UserContext


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
                logging=LoggingPolicy(level="forensic"),
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
                    source="context",
                ),
            )
        ],
        orgs=[
            OrgConfig(
                org_id="test_org",
                default_policy="default_policy",
                filter_name="default_filter",
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
                                    source="context",
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
                                    source="context",
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
                                    source="context",
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
                                    source="context",
                                ),
                                Condition(
                                    field="risk_score",
                                    operator="lte",
                                    value=50,
                                    source="context",
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
                                    source="context",
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
                                    source="context",
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
    assert priorities == [100, 90, 85, 80, 70, 60]


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
        {
            "name": "unknown_org_raises_not_found",
            "user_context": UserContext(
                user_id="u-8",
                org_id="missing_org",
                attributes={},
            ),
            "expected_policy": None,
            "expected_exception": GovernanceOrgNotFoundError,
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
        if isinstance(error, GovernanceOrgNotFoundError):
            assert error.user_context == case["user_context"], case["name"]
