"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from datetime import datetime
from typing import Any, Dict, Iterator

from pydantic import BaseModel, ConfigDict, Field


class LLMUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMMetadata(BaseModel):
    model: str
    provider: str
    latency_ms: float
    request_id: str | None = None
    timestamp: datetime | None = None
    temperature: float | None = None
    top_p: float | None = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str
    usage: LLMUsage
    metadata: LLMMetadata


class LLMStreamChunk(BaseModel):
    delta: str


class LLMStreamResponse(BaseModel):
    # Pydantic v2 cannot generate a core schema for Iterator[LLMStreamChunk]
    # by default, so allow this runtime stream type explicitly.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    stream: Iterator[LLMStreamChunk]
    usage: LLMUsage | None = None
    metadata: LLMMetadata | None = None
