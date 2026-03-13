"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import TypedDict

import pytest
from pydantic import ValidationError

from rag_control.models.config import ControlPlaneConfig


class _ConditionValidationCase(TypedDict):
    name: str
    payload: dict[str, object]
    should_pass: bool
    expected_error: str | None


def test_condition_validate_value_for_operator_with_multiple_conditions() -> None:
    test_cases: list[_ConditionValidationCase] = [
        {
            "name": "equals_with_value_is_valid",
            "payload": {"field": "role", "operator": "equals", "value": "analyst"},
            "should_pass": True,
            "expected_error": None,
        },
        {
            "name": "equals_without_value_is_invalid",
            "payload": {"field": "role", "operator": "equals"},
            "should_pass": False,
            "expected_error": "value is required for 'equals' operator",
        },
        {
            "name": "numeric_with_int_value_is_valid",
            "payload": {"field": "risk_score", "operator": "lte", "value": 50},
            "should_pass": True,
            "expected_error": None,
        },
        {
            "name": "numeric_with_float_value_is_valid",
            "payload": {"field": "risk_score", "operator": "gt", "value": 50.5},
            "should_pass": True,
            "expected_error": None,
        },
        {
            "name": "numeric_with_string_value_is_invalid",
            "payload": {"field": "risk_score", "operator": "gt", "value": "fifty"},
            "should_pass": False,
            "expected_error": "value must be an int or float for numeric operators",
        },
        {
            "name": "numeric_with_bool_value_is_invalid",
            "payload": {"field": "risk_score", "operator": "gte", "value": True},
            "should_pass": False,
            "expected_error": "Input should be a valid integer",
        },
        {
            "name": "intersects_with_value_is_valid",
            "payload": {"field": "region", "operator": "intersects", "value": "eu"},
            "should_pass": True,
            "expected_error": None,
        },
        {
            "name": "intersects_without_value_is_invalid",
            "payload": {"field": "region", "operator": "intersects"},
            "should_pass": False,
            "expected_error": "value is required for 'intersects' operator",
        },
        {
            "name": "exists_without_value_is_valid",
            "payload": {"field": "session_id", "operator": "exists"},
            "should_pass": True,
            "expected_error": None,
        },
        {
            "name": "exists_with_value_is_valid",
            "payload": {"field": "session_id", "operator": "exists", "value": "ignored"},
            "should_pass": True,
            "expected_error": None,
        },
    ]

    def _build_config_payload(condition_payload: dict[str, object]) -> dict[str, object]:
        return {
            "policies": [
                {
                    "name": "default_policy",
                    "generation": {},
                    "logging": {},
                    "enforcement": {},
                }
            ],
            "filters": [],
            "orgs": [
                {
                    "org_id": "test_org",
                    "default_policy": "default_policy",
                    "policy_rules": [
                        {
                            "name": "test_rule",
                            "priority": 1,
                            "effect": "allow",
                            "apply_policy": "default_policy",
                            "when": {"all": [condition_payload]},
                        }
                    ],
                    "deny_rules": [],
                }
            ],
        }

    for case in test_cases:
        config_payload = _build_config_payload(case["payload"])
        if case["should_pass"]:
            config = ControlPlaneConfig.model_validate(config_payload)
            condition = config.orgs[0].policy_rules[0].when.all
            assert condition is not None, case["name"]
            assert condition[0].field == case["payload"]["field"], case["name"]
            assert condition[0].operator == case["payload"]["operator"], case["name"]
            continue

        assert case["expected_error"] is not None
        with pytest.raises(ValidationError, match=case["expected_error"]):
            ControlPlaneConfig.model_validate(config_payload)
