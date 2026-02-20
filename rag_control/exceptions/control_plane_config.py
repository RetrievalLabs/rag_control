"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from .base import RagControlError


class ControlPlaneConfigValidationError(ValueError, RagControlError):
    """Raised when control plane configuration is invalid."""
