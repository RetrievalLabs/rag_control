from .base import RagControlError


class EmbeddingModelTypeError(TypeError, RagControlError):
    """Raised when an embedding model identifier is not a string."""


class EmbeddingModelValidationError(ValueError, RagControlError):
    """Raised when an embedding model identifier is empty or invalid."""


class EmbeddingModelMismatchError(ValueError, RagControlError):
    """Raised when query and vector store embedding models do not match."""
