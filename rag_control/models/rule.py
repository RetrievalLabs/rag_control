"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, StrictInt, model_validator

from rag_control.exceptions.rule import RuleConditionValidationError

RULE_EFFECT_ALLOW = "allow"
RULE_EFFECT_DENY = "deny"

RULE_OPERATOR_EQUALS = "equals"
RULE_OPERATOR_LT = "lt"
RULE_OPERATOR_LTE = "lte"
RULE_OPERATOR_GT = "gt"
RULE_OPERATOR_GTE = "gte"
RULE_OPERATOR_INTERSECTS = "intersects"
RULE_OPERATOR_EXISTS = "exists"

RULE_NUMERIC_OPERATORS = {
    RULE_OPERATOR_LT,
    RULE_OPERATOR_LTE,
    RULE_OPERATOR_GT,
    RULE_OPERATOR_GTE,
}

Operator = Literal["equals", "lt", "lte", "gt", "gte", "intersects", "exists"]


class Condition(BaseModel):
    field: str
    operator: Operator
    value: Optional[Union[str, StrictInt]] = None
    source: Optional[Literal["context"]] = None

    @model_validator(mode="after")
    def validate_value_for_operator(self) -> "Condition":
        if self.operator == RULE_OPERATOR_EXISTS:
            return self

        if self.operator == RULE_OPERATOR_EQUALS:
            if self.value is None:
                raise RuleConditionValidationError(
                    "value is required for 'equals' operator"
                )
            return self

        if self.operator in RULE_NUMERIC_OPERATORS:
            if not isinstance(self.value, int) or isinstance(self.value, bool):
                raise RuleConditionValidationError(
                    "value must be an int for numeric operators: lt/lte/gt/gte"
                )
            return self

        if self.operator == RULE_OPERATOR_INTERSECTS:
            if self.value is None:
                raise RuleConditionValidationError(
                    "value is required for 'intersects' operator"
                )
            return self

        return self


class LogicalCondition(BaseModel):
    all: Optional[List[Condition]] = None
    any: Optional[List[Condition]] = None


class PolicyRule(BaseModel):
    name: str
    description: Optional[str] = None
    priority: int
    effect: Literal["allow", "deny"]
    apply_policy: Optional[str] = None
    when: LogicalCondition
