from typing import List, Literal

from pydantic import BaseModel, StrictFloat, StrictInt

from .operator import (
    OPERATOR_LT,
    OPERATOR_LTE,
    OPERATOR_GT,
    OPERATOR_GTE,
)

POLICY_RULE_NUMERIC_OPERATORS = {
    OPERATOR_LT,
    OPERATOR_LTE,
    OPERATOR_GT,
    OPERATOR_GTE,
}

POLICY_RULE_EFFECT_ALLOW = "allow"
POLICY_RULE_EFFECT_DENY = "deny"

PolicyRuleOperator = Literal["equals", "lt", "lte", "gt", "gte", "intersects", "exists"]


class PolicyRuleCondition(BaseModel):
    field: str
    operator: PolicyRuleOperator
    value: str | StrictInt | StrictFloat | None = None
    source: Literal["user"] = "user"


class PolicyRuleLogicalCondition(BaseModel):
    all: List[PolicyRuleCondition] | None = None
    any: List[PolicyRuleCondition] | None = None


class PolicyRule(BaseModel):
    name: str
    description: str | None = None
    priority: int
    effect: Literal["allow", "deny"]="allow"
    when: PolicyRuleLogicalCondition
    apply_policy: str