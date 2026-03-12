from typing import List, Literal

from pydantic import BaseModel, StrictFloat, StrictInt

POLICY_RULE_OPERATOR_EQUALS = "equals"
POLICY_RULE_OPERATOR_LT = "lt"
POLICY_RULE_OPERATOR_LTE = "lte"
POLICY_RULE_OPERATOR_GT = "gt"
POLICY_RULE_OPERATOR_GTE = "gte"
POLICY_RULE_OPERATOR_INTERSECTS = "intersects"
POLICY_RULE_OPERATOR_EXISTS = "exists"

POLICY_RULE_NUMERIC_OPERATORS = {
    POLICY_RULE_OPERATOR_LT,
    POLICY_RULE_OPERATOR_LTE,
    POLICY_RULE_OPERATOR_GT,
    POLICY_RULE_OPERATOR_GTE,
}

PolicyRuleOperator = Literal["equals", "lt", "lte", "gt", "gte", "intersects", "exists"]


class PolicyRuleCondition(BaseModel):
    field: str
    operator: PolicyRuleOperator
    value: str | StrictInt | StrictFloat | None = None


class PolicyRuleLogicalCondition(BaseModel):
    all: List[PolicyRuleCondition] | None = None
    any: List[PolicyRuleCondition] | None = None


class PolicyRule(BaseModel):
    name: str
    description: str | None = None
    priority: int
    when: PolicyRuleLogicalCondition
    apply_policy: str