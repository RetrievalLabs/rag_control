from pydantic import BaseModel
from typing import List, Optional, Literal, Union


Operator = Literal["equals", "lt", "lte", "gt", "gte", "intersects"]


class Condition(BaseModel):
    field: str
    operator: Operator
    value: Optional[Union[str, int]] = None
    source: Optional[Literal["context"]] = None


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
