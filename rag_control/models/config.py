"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from pydantic import BaseModel, model_validator

from rag_control.exceptions import ControlPlaneConfigValidationError

from .filter import Filter
from .org import OrgConfig
from .policy import Policy
from .rule import (
    Condition,
    LogicalCondition,
    RULE_NUMERIC_OPERATORS,
    RULE_OPERATOR_EQUALS,
    RULE_OPERATOR_EXISTS,
    RULE_OPERATOR_INTERSECTS,
)


class ControlPlaneConfig(BaseModel):
    policies: list[Policy]
    filters: list[Filter]
    orgs: list[OrgConfig]

    @model_validator(mode="after")
    def validate_references(self) -> "ControlPlaneConfig":
        policy_names = [policy.name for policy in self.policies]
        filter_names = [flt.name for flt in self.filters]
        org_ids = [org.org_id for org in self.orgs]

        if len(policy_names) != len(set(policy_names)):
            raise ControlPlaneConfigValidationError("policies must have unique names")

        if len(filter_names) != len(set(filter_names)):
            raise ControlPlaneConfigValidationError("filters must have unique names")

        if len(org_ids) != len(set(org_ids)):
            raise ControlPlaneConfigValidationError("orgs must have unique org_id values")

        policy_name_set = set(policy_names)
        filter_name_set = set(filter_names)

        for org in self.orgs:
            if org.default_policy not in policy_name_set:
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' default_policy '{org.default_policy}' does not exist"
                )

            if org.filter_name is not None and org.filter_name not in filter_name_set:
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' filter_name '{org.filter_name}' does not exist"
                )

            rule_names = [rule.name for rule in org.policy_rules]
            if len(rule_names) != len(set(rule_names)):
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' policy_rules must have unique names"
                )

            rule_priorities = [rule.priority for rule in org.policy_rules]
            if any(priority <= 0 for priority in rule_priorities):
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' policy_rules priorities must be greater than 0"
                )
            if len(rule_priorities) != len(set(rule_priorities)):
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' policy_rules priorities must be unique"
                )

            for rule in org.policy_rules:
                self._validate_rule_conditions(org.org_id, rule.name, rule.when)
                if rule.apply_policy is not None and rule.apply_policy not in policy_name_set:
                    raise ControlPlaneConfigValidationError(
                        f"org '{org.org_id}' rule '{rule.name}' apply_policy "
                        f"'{rule.apply_policy}' does not exist"
                    )

        return self

    @staticmethod
    def _validate_rule_conditions(org_id: str, rule_name: str, when: LogicalCondition) -> None:
        if when.all is not None:
            for condition in when.all:
                ControlPlaneConfig._validate_rule_condition(org_id, rule_name, condition)
        if when.any is not None:
            for condition in when.any:
                ControlPlaneConfig._validate_rule_condition(org_id, rule_name, condition)

    @staticmethod
    def _validate_rule_condition(org_id: str, rule_name: str, condition: Condition) -> None:
        if condition.operator == RULE_OPERATOR_EXISTS:
            return

        if condition.operator == RULE_OPERATOR_EQUALS:
            if condition.value is None:
                raise ControlPlaneConfigValidationError(
                    f"org '{org_id}' rule '{rule_name}': "
                    "value is required for 'equals' operator"
                )
            return

        if condition.operator in RULE_NUMERIC_OPERATORS:
            if not isinstance(condition.value, (int, float)) or isinstance(
                condition.value, bool
            ):
                raise ControlPlaneConfigValidationError(
                    f"org '{org_id}' rule '{rule_name}': "
                    "value must be an int or float for numeric operators: lt/lte/gt/gte"
                )
            return

        if condition.operator == RULE_OPERATOR_INTERSECTS and condition.value is None:
            raise ControlPlaneConfigValidationError(
                f"org '{org_id}' rule '{rule_name}': "
                "value is required for 'intersects' operator"
            )
