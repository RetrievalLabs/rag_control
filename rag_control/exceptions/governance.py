"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.models.user_context import UserContext

from .base import RagControlError


class GovernanceOrgNotFoundError(RagControlError):
    """Raised when no governance config exists for the requested org."""

    def __init__(self, user_context: UserContext) -> None:
        self.user_context = user_context
        super().__init__(f"governance org not found: '{user_context.org_id}'")


class GovernancePolicyDeniedError(RagControlError):
    """Raised when a deny rule matches and blocks policy resolution."""

    def __init__(self, user_context: UserContext, rule_name: str) -> None:
        self.user_context = user_context
        self.rule_name = rule_name
        super().__init__(
            f"governance policy denied for org '{user_context.org_id}' by rule '{rule_name}'"
        )


class GovernanceUserContextOrgIDRequiredError(RagControlError):
    """Raised when user_context does not provide an org_id."""

    def __init__(self) -> None:
        super().__init__("org_id is required in user_context")


class GovernanceRegistryOrgNotFoundError(RagControlError):
    """Raised when org_id cannot be found in the governance registry."""

    def __init__(self, org_id: str) -> None:
        self.org_id = org_id
        super().__init__(f"org_id '{org_id}' not found in governance registry")
