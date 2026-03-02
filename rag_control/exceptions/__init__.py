"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from .adapter import (
    AdapterError,
    LLMAdapterError,
    QueryEmbeddingAdapterError,
    VectorStoreAdapterError,
)
from .base import RagControlError
from .control_plane_config import ControlPlaneConfigValidationError
from .embedding_model import (
    EmbeddingModelMismatchError,
    EmbeddingModelTypeError,
    EmbeddingModelValidationError,
)
from .governance import (
    GovernanceOrgNotFoundError,
    GovernancePolicyDeniedError,
    GovernanceRegistryOrgNotFoundError,
    GovernanceUserContextOrgIDRequiredError,
)

__all__ = [
    "RagControlError",
    "AdapterError",
    "LLMAdapterError",
    "QueryEmbeddingAdapterError",
    "VectorStoreAdapterError",
    "ControlPlaneConfigValidationError",
    "EmbeddingModelTypeError",
    "EmbeddingModelValidationError",
    "EmbeddingModelMismatchError",
    "GovernanceOrgNotFoundError",
    "GovernancePolicyDeniedError",
    "GovernanceUserContextOrgIDRequiredError",
    "GovernanceRegistryOrgNotFoundError",
]
