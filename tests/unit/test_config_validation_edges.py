"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from rag_control.exceptions import ControlPlaneConfigValidationError
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.filter import Condition as FilterCondition
from rag_control.models.filter import Filter


def test_control_plane_config_validate_reference_error_branches(
    fake_config: ControlPlaneConfig,
) -> None:
    base = fake_config.model_dump()
    cases: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
        (
            "duplicate_policy_names",
            lambda payload: payload["policies"].append(payload["policies"][0].copy()),
            "policies must have unique names",
        ),
        (
            "duplicate_filter_names",
            lambda payload: payload["filters"].append(payload["filters"][0].copy()),
            "filters must have unique names",
        ),
        (
            "duplicate_org_ids",
            lambda payload: payload["orgs"].append(payload["orgs"][0].copy()),
            "orgs must have unique org_id values",
        ),
        (
            "org_default_policy_missing",
            lambda payload: payload["orgs"][0].update({"default_policy": "missing"}),
            "default_policy 'missing' does not exist",
        ),
        (
            "org_filter_name_missing",
            lambda payload: payload["orgs"][0]["document_policy"].update({"filter_name": "missing"}),
            "document_policy.filter_name 'missing' does not exist",
        ),
        (
            "duplicate_rule_names",
            lambda payload: payload["orgs"][0]["policy_rules"].append(
                payload["orgs"][0]["policy_rules"][0].copy()
            ),
            "policy_rules must have unique names",
        ),
        (
            "non_positive_rule_priority",
            lambda payload: payload["orgs"][0]["policy_rules"][0].update({"priority": 0}),
            "policy_rules priorities must be greater than 0",
        ),
        (
            "duplicate_rule_priorities",
            lambda payload: payload["orgs"][0]["policy_rules"].append(
                {
                    "name": "allow_enterprise_2",
                    "priority": payload["orgs"][0]["policy_rules"][0]["priority"],
                    "effect": "allow",
                    "apply_policy": "default_policy",
                    "when": {
                        "all": [
                            {
                                "field": "org_tier",
                                "operator": "equals",
                                "value": "enterprise",
                                "source": "user",
                            }
                        ]
                    },
                }
            ),
            "policy_rules priorities must be unique",
        ),
        (
            "apply_policy_missing",
            lambda payload: payload["orgs"][0]["policy_rules"][0].update(
                {"apply_policy": "missing"}
            ),
            "apply_policy 'missing' does not exist",
        ),
    ]

    for _, mutate_payload, expected_error in cases:
        payload = base.copy()
        payload["policies"] = [policy.copy() for policy in base["policies"]]
        payload["filters"] = [flt.copy() for flt in base["filters"]]
        payload["orgs"] = [org.copy() for org in base["orgs"]]
        payload["orgs"][0]["policy_rules"] = [
            rule.copy() for rule in base["orgs"][0]["policy_rules"]
        ]
        payload["orgs"][0]["document_policy"] = base["orgs"][0]["document_policy"].copy()
        mutate_payload(payload)
        with pytest.raises(ValidationError, match=expected_error):
            ControlPlaneConfig.model_validate(payload)


def test_validate_filter_branches_and_filter_condition_branches() -> None:
    valid_condition = FilterCondition(
        field="org_tier",
        operator="equals",
        value="enterprise",
        source="user",
    )

    with pytest.raises(ControlPlaneConfigValidationError, match="must not be empty"):
        ControlPlaneConfig._validate_filter("f", Filter.model_validate({"name": "f", "and": []}))

    with pytest.raises(ControlPlaneConfigValidationError, match="must not be empty"):
        ControlPlaneConfig._validate_filter("f", Filter.model_validate({"name": "f", "or": []}))

    ControlPlaneConfig._validate_filter(
        "f",
        Filter.model_validate(
            {
                "name": "f",
                "and": [{"name": "c1", "condition": valid_condition.model_dump()}],
            }
        ),
    )
    ControlPlaneConfig._validate_filter(
        "f",
        Filter.model_validate(
            {
                "name": "f",
                "or": [{"name": "c2", "condition": valid_condition.model_dump()}],
            }
        ),
    )

    ControlPlaneConfig._validate_filter_condition(
        "f",
        "root",
        FilterCondition(field="x", operator="exists", source="user"),
    )

    with pytest.raises(
        ControlPlaneConfigValidationError,
        match="must not be empty for 'in' operator",
    ):
        ControlPlaneConfig._validate_filter_condition(
            "f",
            "root",
            FilterCondition(field="x", operator="in", value=[], source="user"),
        )
    ControlPlaneConfig._validate_filter_condition(
        "f",
        "root",
        FilterCondition(field="x", operator="in", value=["a"], source="user"),
    )

    with pytest.raises(
        ControlPlaneConfigValidationError,
        match="value is required for 'equals' operator",
    ):
        ControlPlaneConfig._validate_filter_condition(
            "f",
            "root",
            FilterCondition(field="x", operator="equals", value=None, source="user"),
        )

    with pytest.raises(
        ControlPlaneConfigValidationError,
        match="value must be an int or float for numeric operators",
    ):
        ControlPlaneConfig._validate_filter_condition(
            "f",
            "root",
            FilterCondition(field="x", operator="gte", value="oops", source="user"),
        )
    ControlPlaneConfig._validate_filter_condition(
        "f",
        "root",
        FilterCondition(field="x", operator="gte", value=2, source="user"),
    )

    with pytest.raises(
        ControlPlaneConfigValidationError,
        match="value is required for 'intersects' operator",
    ):
        ControlPlaneConfig._validate_filter_condition(
            "f",
            "root",
            FilterCondition(field="x", operator="intersects", value=None, source="user"),
        )
