"""
Copyright (c) 2026. All rights reserved.
Licensed under the Apache License 2.0.
"""

from .base import RagControlError


class EnforcementPolicyViolationError(RagControlError):
    """Raised when a generated response violates enforcement policy checks."""

    def __init__(self, policy_name: str, violations: list[str]) -> None:
        self.policy_name = policy_name
        self.violations = violations
        super().__init__(f"policy '{policy_name}' enforcement failed: " + "; ".join(violations))
