"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import List, Literal, Optional, Union

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


class Condition(BaseModel):
    field: str
    operator: Operator
    value: Optional[Union[str, StrictInt, StrictFloat]] = None
    source: Optional[Literal["context", "source_document"]] = None
    document_match: Optional[DocumentMatchOperator] = None


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
