"""
Copyright (c) 2026. All rights reserved.
Licensed under the Apache License 2.0.
"""

from .base import RagControlError


class ControlPlaneConfigValidationError(ValueError, RagControlError):
    """Raised when control plane configuration is invalid."""
