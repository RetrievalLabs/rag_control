from pydantic import BaseModel
from typing import Dict, List


class OverrideRule(BaseModel):
    name: str
    when: Dict[str, str | int]
    apply_policy: str


class AccessControlPolicy(BaseModel):
    require_match: List[str]
    override_rules: List[OverrideRule]
