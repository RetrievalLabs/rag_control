from pydantic import BaseModel, Field

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
    name: str
    description: Optional[str] = None
    and_: Optional[List["Filter"]] = Field(default=None, alias="and")
    or_: Optional[List["Filter"]] = Field(default=None, alias="or")
    condition: Optional[Condition] = None

    class Config:
        allow_population_by_field_name = True
    
