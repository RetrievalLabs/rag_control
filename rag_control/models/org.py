"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pydantic import BaseModel, Field

from .policy_rule import PolicyRule
from .document import DocumentPolicy
from .deny_rule import DenyRule


class OrgConfig(BaseModel):
    org_id: str
    description: str | None = None
    default_policy: str
    policy_rules: list[PolicyRule]
    deny_rules: list[DenyRule]
