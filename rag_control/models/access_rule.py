"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import List, Literal

from pydantic import BaseModel, StrictFloat, StrictInt

ACCESS_RULE_EFFECT_ALLOW = "allow"
ACCESS_RULE_EFFECT_DENY = "deny"

ACCESS_RULE_OPERATOR_EQUALS = "equals"
ACCESS_RULE_OPERATOR_LT = "lt"
ACCESS_RULE_OPERATOR_LTE = "lte"
ACCESS_RULE_OPERATOR_GT = "gt"
ACCESS_RULE_OPERATOR_GTE = "gte"
ACCESS_RULE_OPERATOR_INTERSECTS = "intersects"
ACCESS_RULE_OPERATOR_EXISTS = "exists"

ACCESS_RULE_NUMERIC_OPERATORS = {
    ACCESS_RULE_OPERATOR_LT,
    ACCESS_RULE_OPERATOR_LTE,
    ACCESS_RULE_OPERATOR_GT,
    ACCESS_RULE_OPERATOR_GTE,
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
