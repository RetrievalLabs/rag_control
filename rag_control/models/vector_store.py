from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class VectorStoreRecord:
    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VectorStoreSearchMetadata:
    provider: str
    index: str
    latency_ms: float
    top_k: int
    returned: int
    request_id: str | None = None
    timestamp: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VectorStoreSearchResponse:
    records: list[VectorStoreRecord]
    metadata: VectorStoreSearchMetadata
