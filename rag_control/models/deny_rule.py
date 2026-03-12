"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import List, Literal

from pydantic import BaseModel, StrictFloat, StrictInt

from .operator import (
    OPERATOR_LT,
    OPERATOR_LTE,
    OPERATOR_GT,
    OPERATOR_GTE,
)

DENY_RULE_NUMERIC_OPERATORS = {
    OPERATOR_LT,
    OPERATOR_LTE,
    OPERATOR_GT,
    OPERATOR_GTE,
}

DenyRuleOperator = Literal["equals", "lt", "lte", "gt", "gte", "intersects", "exists"]
DenyRuleConditionSource = Literal["user", "documents"]
DenyRuleDocumentMatchOperator = Literal["any", "all"]


class DenyRuleCondition(BaseModel):
    field: str
    operator: DenyRuleOperator
    value: str | StrictInt | StrictFloat | None = None
    source: DenyRuleConditionSource = "user"
    document_match: DenyRuleDocumentMatchOperator | None = None


class DenyRuleLogicalCondition(BaseModel):
    all: List[DenyRuleCondition] | None = None
    any: List[DenyRuleCondition] | None = None


class DenyRule(BaseModel):
    name: str
    description: str | None = None
    priority: int
    when: DenyRuleLogicalCondition
