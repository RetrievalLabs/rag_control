"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pydantic import BaseModel, ConfigDict, Field

from typing import Literal, Optional, List, Union

Operator = Literal[
    "equals",
    "in",
    "intersects",
    "lte",
    "gte"
]

class Condition(BaseModel):
    field: str
    operator: Operator
    value: Optional[Union[str, int, List[str], List[int]]] = None
    source: Literal["context"] = "context"


class Filter(BaseModel):
    # Accept both field names (`and_`/`or_`) and aliases (`and`/`or`) in input.
    model_config = ConfigDict(validate_by_name=True)

    name: str
    description: Optional[str] = None
    and_: Optional[List["Filter"]] = Field(default=None, alias="and")
    or_: Optional[List["Filter"]] = Field(default=None, alias="or")
    condition: Optional[Condition] = None
    
