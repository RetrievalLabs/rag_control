"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from pydantic import BaseModel, model_validator

from rag_control.exceptions import ControlPlaneConfigValidationError

from .operator import (
    OPERATOR_EQUALS,
    OPERATOR_IN,
    OPERATOR_INTERSECTS,
    OPERATOR_EXISTS,
)
from .filter import Filter, FilterCondition, FILTER_NUMERIC_OPERATORS
from .org import OrgConfig
from .policy import Policy
from .deny_rule import (
    DenyRuleCondition,
    DenyRuleLogicalCondition,
    DENY_RULE_NUMERIC_OPERATORS,
)
from .policy_rule import (
    PolicyRuleCondition,
    PolicyRuleLogicalCondition,
    POLICY_RULE_NUMERIC_OPERATORS,
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

        filter_name_set = set(filter_names)

        for policy in self.policies:
            if not (0.0 <= policy.generation.temperature <= 2.0):
                raise ControlPlaneConfigValidationError(
                    f"policy '{policy.name}' generation.temperature must be between 0.0 and 2.0"
                )
            if policy.document_policy.top_k <= 0:
                raise ControlPlaneConfigValidationError(
                    f"policy '{policy.name}' document_policy.top_k must be greater than 0"
                )
            if policy.document_policy.filter_name is not None and policy.document_policy.filter_name not in filter_name_set:
                raise ControlPlaneConfigValidationError(
                    f"policy '{policy.name}' document_policy.filter_name '{policy.document_policy.filter_name}' does not exist"
                )

        if len(org_ids) != len(set(org_ids)):
            raise ControlPlaneConfigValidationError("orgs must have unique org_id values")

        policy_name_set = set(policy_names)

        for flt in self.filters:
            self._validate_filter(flt.name, flt)

        for org in self.orgs:
            if org.default_policy not in policy_name_set:
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' default_policy '{org.default_policy}' does not exist"
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
                self._validate_rule_conditions(org.org_id, rule.name, rule.when, is_deny_rule=False)
                if rule.effect == "allow" and rule.apply_policy is None:
                    raise ControlPlaneConfigValidationError(
                        f"org '{org.org_id}' rule '{rule.name}' with effect='allow' must specify apply_policy"
                    )
                if rule.apply_policy is not None and rule.apply_policy not in policy_name_set:
                    raise ControlPlaneConfigValidationError(
                        f"org '{org.org_id}' rule '{rule.name}' apply_policy "
                        f"'{rule.apply_policy}' does not exist"
                    )

            deny_rule_names = [rule.name for rule in org.deny_rules]
            if len(deny_rule_names) != len(set(deny_rule_names)):
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' deny_rules must have unique names"
                )

            deny_rule_priorities = [rule.priority for rule in org.deny_rules]
            if any(priority <= 0 for priority in deny_rule_priorities):
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' deny_rules priorities must be greater than 0"
                )
            if len(deny_rule_priorities) != len(set(deny_rule_priorities)):
                raise ControlPlaneConfigValidationError(
                    f"org '{org.org_id}' deny_rules priorities must be unique"
                )

            for rule in org.deny_rules:
                self._validate_rule_conditions(org.org_id, rule.name, rule.when, is_deny_rule=True)

        return self

    @staticmethod
    def _validate_rule_conditions(
        org_id: str,
        rule_name: str,
        when: DenyRuleLogicalCondition | PolicyRuleLogicalCondition,
        is_deny_rule: bool = True,
    ) -> None:
        if when.all is not None:
            for condition in when.all:
                ControlPlaneConfig._validate_rule_condition(
                    org_id, rule_name, condition, is_deny_rule
                )
        if when.any is not None:
            for condition in when.any:
                ControlPlaneConfig._validate_rule_condition(
                    org_id, rule_name, condition, is_deny_rule
                )

    @staticmethod
    def _validate_rule_condition(
        org_id: str,
        rule_name: str,
        condition: DenyRuleCondition | PolicyRuleCondition,
        is_deny_rule: bool = True,
    ) -> None:
        if (
            is_deny_rule
            and hasattr(condition, "document_match")
            and condition.document_match is not None
            and condition.source != "documents"
        ):
            raise ControlPlaneConfigValidationError(
                f"org '{org_id}' rule '{rule_name}': "
                "document_match is only supported when source is 'documents'"
            )

        if condition.operator == OPERATOR_EXISTS:
            return

        if condition.operator == OPERATOR_EQUALS:
            if condition.value is None:
                raise ControlPlaneConfigValidationError(
                    f"org '{org_id}' rule '{rule_name}': value is required for 'equals' operator"
                )
            return

        if is_deny_rule and condition.operator in DENY_RULE_NUMERIC_OPERATORS:
            if not isinstance(condition.value, (int, float)) or isinstance(condition.value, bool):
                raise ControlPlaneConfigValidationError(
                    f"org '{org_id}' rule '{rule_name}': "
                    "value must be an int or float for numeric operators: lt/lte/gt/gte"
                )
            return

        if not is_deny_rule and condition.operator in POLICY_RULE_NUMERIC_OPERATORS:
            if not isinstance(condition.value, (int, float)) or isinstance(condition.value, bool):
                raise ControlPlaneConfigValidationError(
                    f"org '{org_id}' rule '{rule_name}': "
                    "value must be an int or float for numeric operators: lt/lte/gt/gte"
                )
            return

        if condition.operator == OPERATOR_INTERSECTS and condition.value is None:
            raise ControlPlaneConfigValidationError(
                f"org '{org_id}' rule '{rule_name}': value is required for 'intersects' operator"
            )

    @staticmethod
    def _validate_filter(filter_name: str, flt: Filter, path: str = "root") -> None:
        defined_nodes = sum(
            [
                flt.condition is not None,
                flt.and_ is not None,
                flt.or_ is not None,
            ]
        )
        if defined_nodes != 1:
            raise ControlPlaneConfigValidationError(
                f"filter '{filter_name}' at '{path}' must include exactly one of: "
                "condition, and, or"
            )

        if flt.condition is not None:
            ControlPlaneConfig._validate_filter_condition(filter_name, path, flt.condition)

        if flt.and_ is not None:
            if len(flt.and_) == 0:
                raise ControlPlaneConfigValidationError(
                    f"filter '{filter_name}' at '{path}.and' must not be empty"
                )
            for index, child_filter in enumerate(flt.and_):
                ControlPlaneConfig._validate_filter(
                    filter_name, child_filter, path=f"{path}.and[{index}]"
                )

        if flt.or_ is not None:
            if len(flt.or_) == 0:
                raise ControlPlaneConfigValidationError(
                    f"filter '{filter_name}' at '{path}.or' must not be empty"
                )
            for index, child_filter in enumerate(flt.or_):
                ControlPlaneConfig._validate_filter(
                    filter_name, child_filter, path=f"{path}.or[{index}]"
                )

    @staticmethod
    def _validate_filter_condition(filter_name: str, path: str, condition: FilterCondition) -> None:
        if condition.operator == OPERATOR_EXISTS:
            return

        if condition.operator == OPERATOR_IN:
            if not isinstance(condition.value, list):
                raise ControlPlaneConfigValidationError(
                    f"filter '{filter_name}' at '{path}': value must be a list for 'in' operator"
                )
            if len(condition.value) == 0:
                raise ControlPlaneConfigValidationError(
                    f"filter '{filter_name}' at '{path}': value must not be empty for 'in' operator"
                )
            return

        if condition.operator == OPERATOR_EQUALS:
            if condition.value is None:
                raise ControlPlaneConfigValidationError(
                    f"filter '{filter_name}' at '{path}': value is required for 'equals' operator"
                )
            return

        if condition.operator in FILTER_NUMERIC_OPERATORS:
            if not isinstance(condition.value, (int, float)) or isinstance(condition.value, bool):
                raise ControlPlaneConfigValidationError(
                    f"filter '{filter_name}' at '{path}': "
                    "value must be an int or float for numeric operators: lt/lte/gt/gte"
                )
            return

        if condition.operator == OPERATOR_INTERSECTS and condition.value is None:
            raise ControlPlaneConfigValidationError(
                f"filter '{filter_name}' at '{path}': value is required for 'intersects' operator"
            )
