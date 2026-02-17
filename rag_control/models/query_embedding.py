from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class QueryEmbeddingMetadata:
    model: str
    provider: str
    latency_ms: float
    dimensions: int
    request_id: str | None = None
    timestamp: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QueryEmbeddingResponse:
    embedding: list[float]
    metadata: QueryEmbeddingMetadata
