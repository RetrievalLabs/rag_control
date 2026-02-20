"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QueryEmbeddingMetadata(BaseModel):
    model: str
    provider: str
    latency_ms: float
    dimensions: int
    request_id: str | None = None
    timestamp: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class QueryEmbeddingResponse(BaseModel):
    embedding: list[float]
    metadata: QueryEmbeddingMetadata
