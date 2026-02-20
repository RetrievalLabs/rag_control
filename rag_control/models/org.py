from pydantic import BaseModel

from .rule import PolicyRule


class OrgConfig(BaseModel):
    org_id: str
    description: str | None = None
    default_policy: str
    policy_rules: list[PolicyRule]
    filter_name: str | None = None
