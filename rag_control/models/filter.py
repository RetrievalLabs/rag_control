"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field

from .operator import (
    OPERATOR_GT,
    OPERATOR_GTE,
    OPERATOR_LT,
    OPERATOR_LTE,
)

FILTER_NUMERIC_OPERATORS = {
    OPERATOR_LT,
    OPERATOR_LTE,
    OPERATOR_GT,
    OPERATOR_GTE,
}

FilterOperator = Literal["equals", "in", "intersects", "lt", "lte", "gt", "gte", "exists"]


class FilterCondition(BaseModel):
    field: str
    operator: FilterOperator
    value: str | int | List[str] | List[int] | None = None
    source: Literal["user"] = "user"


class Filter(BaseModel):
    # Accept both field names (`and_`/`or_`) and aliases (`and`/`or`) in input.
    model_config = ConfigDict(validate_by_name=True)

    name: str
    description: str | None = None
    and_: List["Filter"] | None = Field(default=None, alias="and")
    or_: List["Filter"] | None = Field(default=None, alias="or")
    condition: FilterCondition | None = None
