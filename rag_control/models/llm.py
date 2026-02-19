"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from datetime import datetime
from typing import Any, Dict, Iterator, Optional

from pydantic import BaseModel, Field


class LLMUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMMetadata(BaseModel):
    model: str
    provider: str
    latency_ms: float
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str
    usage: LLMUsage
    metadata: LLMMetadata


class LLMStreamChunk(BaseModel):
    delta: str


class LLMStreamResponse(BaseModel):
    stream: Iterator[LLMStreamChunk]
    usage: Optional[LLMUsage] = None
    metadata: Optional[LLMMetadata] = None
