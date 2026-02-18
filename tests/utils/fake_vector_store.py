from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from rag_control.adapters.vector_store import VectorStore
from rag_control.models.vector_store import (
    VectorStoreRecord,
    VectorStoreSearchMetadata,
    VectorStoreSearchResponse,
)


@dataclass(slots=True)
class _PlannedSearch:
    records: list[VectorStoreRecord]
    provider: str
    index: str
    latency_ms: float
    request_id: str | None = None
    timestamp: datetime | None = None


class FakeVectorStore(VectorStore):
    """Deterministic, in-memory vector store adapter for tests."""

    def __init__(
        self,
        *,
        default_records: list[VectorStoreRecord] | None = None,
        provider: str = "fake-vector-store",
        index: str = "fake-index",
        latency_ms: float = 0.0,
    ) -> None:
        self.default_records = default_records or [
            VectorStoreRecord(id="doc-1", content="default", score=1.0, metadata={})
        ]
        self.default_provider = provider
        self.default_index = index
        self.default_latency_ms = latency_ms

        self.search_calls = 0
        self.embeddings: list[list[float]] = []
        self.top_ks: list[int] = []

        self._planned_outputs: list[_PlannedSearch] = []
        self._next_error: Exception | None = None

    def enqueue_response(
        self,
        *,
        records: list[VectorStoreRecord],
        provider: str | None = None,
        index: str | None = None,
        latency_ms: float | None = None,
        request_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        self._planned_outputs.append(
            _PlannedSearch(
                records=records,
                provider=provider or self.default_provider,
                index=index or self.default_index,
                latency_ms=self.default_latency_ms if latency_ms is None else latency_ms,
                request_id=request_id,
                timestamp=timestamp,
            )
        )

    def fail_next(self, error: Exception) -> None:
        self._next_error = error

    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> VectorStoreSearchResponse:
        if self._next_error is not None:
            error = self._next_error
            self._next_error = None
            raise error

        self._validate_embedding(embedding)
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be an int >= 1")

        self.search_calls += 1
        self.embeddings.append(embedding)
        self.top_ks.append(top_k)

        planned = self._next_planned_output()
        records = planned.records[:top_k]

        return VectorStoreSearchResponse(
            records=records,
            metadata=VectorStoreSearchMetadata(
                provider=planned.provider,
                index=planned.index,
                latency_ms=max(0.0, float(planned.latency_ms)),
                top_k=top_k,
                returned=len(records),
                request_id=planned.request_id,
                timestamp=planned.timestamp,
                raw={},
            ),
        )

    def retrieve(self, query_embedding_response: Any, top_k: int = 5) -> VectorStoreSearchResponse:
        embedding = query_embedding_response
        if hasattr(query_embedding_response, "embedding"):
            embedding = query_embedding_response.embedding
        return self.search(embedding=embedding, top_k=top_k)

    def _next_planned_output(self) -> _PlannedSearch:
        if self._planned_outputs:
            return self._planned_outputs.pop(0)
        return _PlannedSearch(
            records=self.default_records,
            provider=self.default_provider,
            index=self.default_index,
            latency_ms=self.default_latency_ms,
        )

    @staticmethod
    def _validate_embedding(embedding: list[float]) -> None:
        if not isinstance(embedding, list):
            raise TypeError("embedding must be a list[float]")

        for value in embedding:
            if not isinstance(value, (int, float)):
                raise TypeError("embedding values must be numeric")
