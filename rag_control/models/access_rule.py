"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import List, Literal

from pydantic import BaseModel, StrictFloat, StrictInt

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
DocumentMatchOperator = Literal["any", "all"]
ConditionSource = Literal["user", "documents"]


class Condition(BaseModel):
    field: str
    operator: Operator
    value: str | StrictInt | StrictFloat | None = None
    source: ConditionSource = "user"
    document_match: DocumentMatchOperator | None = None


class LogicalCondition(BaseModel):
    all: List[Condition] | None = None
    any: List[Condition] | None = None


class AccessRule(BaseModel):
    name: str
    description: str | None = None
    priority: int
    effect: Literal["allow", "deny"]
    when: LogicalCondition
