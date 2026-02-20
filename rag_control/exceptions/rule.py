"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from .base import RagControlError


class RuleConditionValidationError(ValueError, RagControlError):
    """Raised when a policy-rule condition has an invalid value for its operator."""
