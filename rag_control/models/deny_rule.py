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
