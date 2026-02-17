from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from rag_control.adapters.query_embedding import QueryEmbedding
from rag_control.models.query_embedding import (
    QueryEmbeddingMetadata,
    QueryEmbeddingResponse,
)


@dataclass(slots=True)
class _PlannedEmbedding:
    embedding: list[float]
    model: str
    provider: str
    latency_ms: float
    dimensions: int
    request_id: str | None = None
    timestamp: datetime | None = None


class FakeQueryEmbedding(QueryEmbedding):
    """Deterministic, in-memory query embedding adapter for tests."""

    def __init__(
        self,
        *,
        default_embedding: list[float] | None = None,
        model: str = "fake-embedding-model",
        provider: str = "fake-provider",
        latency_ms: float = 0.0,
    ) -> None:
        self.default_embedding = default_embedding or [0.0, 0.0, 0.0]
        self.default_model = model
        self.default_provider = provider
        self.default_latency_ms = latency_ms

        self.queries: list[str] = []
        self.embed_calls = 0
        self._planned_outputs: list[_PlannedEmbedding] = []
        self._next_error: Exception | None = None

    def enqueue_response(
        self,
        *,
        embedding: list[float],
        model: str | None = None,
        provider: str | None = None,
        latency_ms: float | None = None,
        request_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        self._planned_outputs.append(
            _PlannedEmbedding(
                embedding=embedding,
                model=model or self.default_model,
                provider=provider or self.default_provider,
                latency_ms=self.default_latency_ms if latency_ms is None else latency_ms,
                dimensions=len(embedding),
                request_id=request_id,
                timestamp=timestamp,
            )
        )

    def fail_next(self, error: Exception) -> None:
        self._next_error = error

    def embed(self, query: str) -> QueryEmbeddingResponse:
        if self._next_error is not None:
            error = self._next_error
            self._next_error = None
            raise error

        self._validate_query(query)
        self.queries.append(query)
        self.embed_calls += 1

        planned = self._next_planned_output()
        return QueryEmbeddingResponse(
            embedding=planned.embedding,
            metadata=QueryEmbeddingMetadata(
                model=planned.model,
                provider=planned.provider,
                latency_ms=max(0.0, float(planned.latency_ms)),
                dimensions=max(0, planned.dimensions),
                request_id=planned.request_id,
                timestamp=planned.timestamp,
                raw={},
            ),
        )

    def _next_planned_output(self) -> _PlannedEmbedding:
        if self._planned_outputs:
            return self._planned_outputs.pop(0)
        return _PlannedEmbedding(
            embedding=self.default_embedding,
            model=self.default_model,
            provider=self.default_provider,
            latency_ms=self.default_latency_ms,
            dimensions=len(self.default_embedding),
        )

    @staticmethod
    def _validate_query(query: str) -> None:
        if not isinstance(query, str):
            raise TypeError("query must be a str")
