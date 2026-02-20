"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import Any

from rag_control.exceptions import (
    GovernanceOrgNotFoundError,
    GovernancePolicyDeniedError,
)
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.org import OrgConfig
from rag_control.models.rule import (
    Condition,
    LogicalCondition,
    PolicyRule,
    RULE_EFFECT_DENY,
    RULE_NUMERIC_OPERATORS,
    RULE_OPERATOR_EQUALS,
    RULE_OPERATOR_GT,
    RULE_OPERATOR_GTE,
    RULE_OPERATOR_INTERSECTS,
    RULE_OPERATOR_LT,
    RULE_OPERATOR_LTE,
)
from rag_control.models.user_context import UserContext


class GovernanceRegistry:
    def __init__(self, config: ControlPlaneConfig):
        self.org_map: dict[str, OrgConfig] = {
            org.org_id: org.model_copy(
                update={
                    "policy_rules": sorted(
                        org.policy_rules,
                        key=lambda policy_rule: policy_rule.priority,
                        reverse=True,
                    )
                }
            )
            for org in config.orgs
        }

    def get_org(self, org_name: str) -> OrgConfig | None:
        return self.org_map.get(org_name)

    def resolve_policy(self, user_context: UserContext) -> str:
        org = self.get_org(user_context.org_id)
        if org is None:
            raise GovernanceOrgNotFoundError(user_context)

        default_policy = org.default_policy
        context = user_context.attributes

        for rule in org.policy_rules:
            if not self._matches_logical_condition(rule.when, context):
                continue
            if rule.effect == RULE_EFFECT_DENY:
                raise GovernancePolicyDeniedError(user_context, rule.name)
            if rule.apply_policy is not None:
                return rule.apply_policy
            return default_policy

        return default_policy

    @staticmethod
    def _matches_logical_condition(
        logical_condition: LogicalCondition, context: dict[str, Any]
    ) -> bool:
        all_conditions = logical_condition.all
        any_conditions = logical_condition.any

        has_all = all_conditions is not None
        has_any = any_conditions is not None

        if not has_all and not has_any:
            return False

        all_match = (
            len(all_conditions) > 0
            and all(
                GovernanceRegistry._matches_condition(condition, context)
                for condition in all_conditions
            )
            if all_conditions is not None
            else False
        )

        any_match = (
            len(any_conditions) > 0
            and any(
                GovernanceRegistry._matches_condition(condition, context)
                for condition in any_conditions
            )
            if any_conditions is not None
            else False
        )

        if has_all and has_any:
            return all_match or any_match

        return all_match if has_all else any_match

    @staticmethod
    def _matches_condition(condition: Condition, context: dict[str, Any]) -> bool:
        actual_value = context.get(condition.field)
        expected_value = condition.value
        operator = condition.operator

        if operator == RULE_OPERATOR_EQUALS:
            return actual_value == expected_value

        if expected_value is None:
            return False

        if operator in RULE_NUMERIC_OPERATORS:
            if not isinstance(actual_value, (int, float)) or not isinstance(
                expected_value, (int, float)
            ):
                return False
            if operator == RULE_OPERATOR_LT:
                return actual_value < expected_value
            if operator == RULE_OPERATOR_LTE:
                return actual_value <= expected_value
            if operator == RULE_OPERATOR_GT:
                return actual_value > expected_value
            if operator == RULE_OPERATOR_GTE:
                return actual_value >= expected_value
            return actual_value >= expected_value

        if operator == RULE_OPERATOR_INTERSECTS:
            if isinstance(actual_value, (list, set, tuple)):
                return expected_value in actual_value
            if isinstance(actual_value, str) and isinstance(expected_value, str):
                return expected_value in actual_value
            return False

        return False
