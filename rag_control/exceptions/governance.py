"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.models.user_context import UserContext

from .base import RagControlError


class GovernanceResolutionError(RagControlError):
    """Base exception for governance policy-resolution failures."""


class GovernanceOrgNotFoundError(GovernanceResolutionError):
    """Raised when no governance config exists for the requested org."""

    def __init__(self, user_context: UserContext) -> None:
        self.user_context = user_context
        super().__init__(f"governance org not found: '{user_context.org_id}'")


class GovernancePolicyDeniedError(GovernanceResolutionError):
    """Raised when a deny rule matches and blocks policy resolution."""

    def __init__(self, user_context: UserContext, rule_name: str) -> None:
        self.user_context = user_context
        self.rule_name = rule_name
        super().__init__(
            f"governance policy denied for org '{user_context.org_id}' by rule '{rule_name}'"
        )
