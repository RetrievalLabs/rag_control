"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import Any

from rag_control.exceptions.governance import (
    GovernanceOrgNotFoundError,
    GovernancePolicyDeniedError,
)
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.org import OrgConfig
from rag_control.models.rule import (
    RULE_EFFECT_DENY,
    RULE_NUMERIC_OPERATORS,
    RULE_OPERATOR_EQUALS,
    RULE_OPERATOR_EXISTS,
    RULE_OPERATOR_GT,
    RULE_OPERATOR_GTE,
    RULE_OPERATOR_INTERSECTS,
    RULE_OPERATOR_LT,
    RULE_OPERATOR_LTE,
    Condition,
    LogicalCondition,
)
from rag_control.models.user_context import UserContext
from rag_control.models.vector_store import VectorStoreRecord


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

    def resolve_policy(
        self,
        user_context: UserContext,
        source_documents: list[VectorStoreRecord] | None = None,
    ) -> str:
        org = self.get_org(user_context.org_id)
        if org is None:
            raise GovernanceOrgNotFoundError(user_context)

        default_policy = org.default_policy
        for rule in org.policy_rules:
            if not self._matches_logical_condition(rule.when, user_context, source_documents):
                continue
            if rule.effect == RULE_EFFECT_DENY:
                raise GovernancePolicyDeniedError(user_context, rule.name)
            if rule.apply_policy is not None:
                return rule.apply_policy
            return default_policy

        return default_policy

    @staticmethod
    def _matches_logical_condition(
        logical_condition: LogicalCondition,
        user_context: UserContext,
        source_documents: list[VectorStoreRecord] | None = None,
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
                GovernanceRegistry._matches_condition(condition, user_context, source_documents)
                for condition in all_conditions
            )
            if all_conditions is not None
            else False
        )

        any_match = (
            len(any_conditions) > 0
            and any(
                GovernanceRegistry._matches_condition(condition, user_context, source_documents)
                for condition in any_conditions
            )
            if any_conditions is not None
            else False
        )

        if has_all and has_any:
            return all_match or any_match

        return all_match if has_all else any_match

    @staticmethod
    def _matches_condition(
        condition: Condition,
        user_context: UserContext,
        source_documents: list[VectorStoreRecord] | None = None,
    ) -> bool:
        if condition.source == "documents":
            return GovernanceRegistry._matches_source_document_condition(
                condition, source_documents or []
            )

        has_field, actual_value = GovernanceRegistry._resolve_user_value(
            user_context, condition.field
        )
        expected_value = condition.value
        operator = condition.operator

        if operator == RULE_OPERATOR_EXISTS:
            return has_field

        if operator == RULE_OPERATOR_EQUALS:
            return bool(actual_value == expected_value)

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

    @staticmethod
    def _resolve_user_value(user_context: UserContext, field: str) -> tuple[bool, Any]:
        root_context = user_context.model_dump()
        attributes = user_context.attributes

        # Backward compatible path: direct attributes lookup for existing rule configs.
        if field in attributes:
            return True, attributes[field]

        # Support top-level fields and custom extra keys on UserContext.
        if field in root_context:
            return True, root_context[field]

        # Support nested paths anywhere in UserContext, e.g. "profile.department"
        # or "attributes.department".
        has_nested, nested_value = GovernanceRegistry._resolve_nested_value(root_context, field)
        if has_nested:
            return True, nested_value

        # Support nested keys in attributes without requiring "attributes." prefix.
        return GovernanceRegistry._resolve_nested_value(attributes, field)

    @staticmethod
    def _matches_source_document_condition(
        condition: Condition, source_documents: list[VectorStoreRecord]
    ) -> bool:
        if len(source_documents) == 0:
            return False

        require_all_docs = condition.document_match == "all"
        document_matches = [
            GovernanceRegistry._matches_condition_for_document(condition, source_document)
            for source_document in source_documents
        ]
        if require_all_docs:
            return all(document_matches)
        return any(document_matches)

    @staticmethod
    def _matches_condition_for_document(
        condition: Condition, source_document: VectorStoreRecord
    ) -> bool:
        source_document_data = source_document.model_dump()
        has_field, actual_value = GovernanceRegistry._resolve_nested_value(
            source_document_data, condition.field
        )
        expected_value = condition.value
        operator = condition.operator

        if operator == RULE_OPERATOR_EXISTS:
            return has_field

        if operator == RULE_OPERATOR_EQUALS:
            return bool(actual_value == expected_value)

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

    @staticmethod
    def _resolve_nested_value(data: dict[str, Any], path: str) -> tuple[bool, Any]:
        current: Any = data
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return False, None
            current = current[key]
        return True, current
