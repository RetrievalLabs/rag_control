from .base import RagControlError


class EmbeddingModelTypeError(TypeError, RagControlError):
    """Raised when an embedding model identifier is not a string."""

    def __init__(self, source: str) -> None:
        super().__init__(f"{source} must be a str")


class EmbeddingModelValidationError(ValueError, RagControlError):
    """Raised when an embedding model identifier is empty or invalid."""

    def __init__(self, source: str) -> None:
        super().__init__(f"{source} must be non-empty")


class EmbeddingModelMismatchError(ValueError, RagControlError):
    """Raised when query and vector store embedding models do not match."""

    _DEFAULT_MESSAGE = "query embedding model must match vector store embedding model"

    def __init__(self, query_model: str, vector_model: str) -> None:
        super().__init__(f"{self._DEFAULT_MESSAGE}: {query_model!r} != {vector_model!r}")
