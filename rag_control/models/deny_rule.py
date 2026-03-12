"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import List, Literal

from pydantic import BaseModel, StrictFloat, StrictInt

DENY_RULE_OPERATOR_EQUALS = "equals"
DENY_RULE_OPERATOR_LT = "lt"
DENY_RULE_OPERATOR_LTE = "lte"
DENY_RULE_OPERATOR_GT = "gt"
DENY_RULE_OPERATOR_GTE = "gte"
DENY_RULE_OPERATOR_INTERSECTS = "intersects"
DENY_RULE_OPERATOR_EXISTS = "exists"

DENY_RULE_NUMERIC_OPERATORS = {
    DENY_RULE_OPERATOR_LT,
    DENY_RULE_OPERATOR_LTE,
    DENY_RULE_OPERATOR_GT,
    DENY_RULE_OPERATOR_GTE,
}

Operator = Literal["equals", "lt", "lte", "gt", "gte", "intersects", "exists"]
ConditionSource = Literal["user", "documents"]
DocumentMatchOperator = Literal["any", "all"]


class Condition(BaseModel):
    field: str
    operator: Operator
    value: str | StrictInt | StrictFloat | None = None
    source: ConditionSource = "user"
    document_match: DocumentMatchOperator | None = None


class LogicalCondition(BaseModel):
    all: List[Condition] | None = None
    any: List[Condition] | None = None


class DenyRule(BaseModel):
    name: str
    description: str | None = None
    priority: int
    when: LogicalCondition
