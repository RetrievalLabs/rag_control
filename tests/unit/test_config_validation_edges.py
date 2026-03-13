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
from rag_control.models.filter import FilterCondition
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
        (
            "allow_rule_without_apply_policy",
            lambda payload: payload["orgs"][0]["policy_rules"][0].update(
                {"apply_policy": None}
            ),
            "effect='allow' must specify apply_policy",
        ),
        (
            "document_policy_filter_name_missing",
            lambda payload: payload["policies"][0]["document_policy"].update(
                {"filter_name": "missing_filter"}
            ),
            "document_policy.filter_name 'missing_filter' does not exist",
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
        payload["orgs"][0]["deny_rules"] = [
            rule.copy() for rule in base["orgs"][0].get("deny_rules", [])
        ]
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


def test_temperature_validation(fake_config: ControlPlaneConfig) -> None:
    """Test temperature validation bounds."""
    from pydantic import ValidationError

    config_dict = fake_config.model_dump()

    # Test temperature too high
    config_dict["policies"][0]["generation"]["temperature"] = 2.5
    with pytest.raises(ValidationError, match="generation.temperature must be between 0.0 and 2.0"):
        ControlPlaneConfig.model_validate(config_dict)

    # Test temperature too low
    config_dict = fake_config.model_dump()
    config_dict["policies"][0]["generation"]["temperature"] = -0.1
    with pytest.raises(ValidationError, match="generation.temperature must be between 0.0 and 2.0"):
        ControlPlaneConfig.model_validate(config_dict)


def test_deny_rule_condition_with_document_match_and_wrong_source() -> None:
    """Test deny rule with document_match but source != documents."""
    from pydantic import ValidationError

    config_dict = {
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
                "policy_rules": [],
                "deny_rules": [
                    {
                        "name": "invalid_doc_match",
                        "priority": 100,
                        "when": {
                            "any": [{
                                "field": "x",
                                "operator": "equals",
                                "value": "y",
                                "source": "user",  # user source, not documents
                                "document_match": "any"  # Invalid with user source
                            }]
                        }
                    }
                ],
            }
        ],
    }

    with pytest.raises(ValidationError, match="document_match is only supported when source is 'documents'"):
        ControlPlaneConfig.model_validate(config_dict)


def test_deny_rule_numeric_operator_validation() -> None:
    """Test deny rule numeric operator requires numeric value."""
    from pydantic import ValidationError

    config_dict = {
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
                "policy_rules": [],
                "deny_rules": [
                    {
                        "name": "invalid_numeric",
                        "priority": 100,
                        "when": {
                            "any": [{
                                "field": "score",
                                "operator": "gt",
                                "value": "not_a_number",  # Invalid: string for numeric operator
                                "source": "user"
                            }]
                        }
                    }
                ],
            }
        ],
    }

    with pytest.raises(ValidationError, match="value must be an int or float for numeric operators"):
        ControlPlaneConfig.model_validate(config_dict)


def test_deny_rule_validation(fake_config: ControlPlaneConfig) -> None:
    """Test deny rule validations."""
    from pydantic import ValidationError

    config_dict = fake_config.model_dump()

    # Test duplicate deny rule names
    config_dict["orgs"][0]["deny_rules"].append(config_dict["orgs"][0]["deny_rules"][0].copy())
    with pytest.raises(ValidationError, match="deny_rules must have unique names"):
        ControlPlaneConfig.model_validate(config_dict)

    # Test deny rule priority zero
    config_dict = fake_config.model_dump()
    config_dict["orgs"][0]["deny_rules"][0]["priority"] = 0
    with pytest.raises(ValidationError, match="deny_rules priorities must be greater than 0"):
        ControlPlaneConfig.model_validate(config_dict)

    # Test duplicate deny rule priorities
    config_dict = fake_config.model_dump()
    config_dict["orgs"][0]["deny_rules"].append({
        "name": "deny_duplicate",
        "priority": config_dict["orgs"][0]["deny_rules"][0]["priority"],
        "when": {"any": [{"field": "x", "operator": "equals", "value": "y", "source": "user"}]}
    })
    with pytest.raises(ValidationError, match="deny_rules priorities must be unique"):
        ControlPlaneConfig.model_validate(config_dict)
