"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterator, Optional


@dataclass(slots=True)
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(slots=True)
class LLMMetadata:
    model: str
    provider: str
    latency_ms: float
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LLMResponse:
    content: str
    usage: LLMUsage
    metadata: LLMMetadata


@dataclass(slots=True)
class LLMStreamChunk:
    delta: str


@dataclass(slots=True)
class LLMStreamResponse:
    stream: Iterator[LLMStreamChunk]
    usage: Optional[LLMUsage] = None
    metadata: Optional[LLMMetadata] = None
