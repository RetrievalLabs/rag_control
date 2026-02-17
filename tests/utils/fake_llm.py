from typing import Any, Dict, Iterator, Optional


class LLMUsage:
    def __init__(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class LLMMetadata:
    def __init__(
        self,
        model: str,
        provider: str,
        latency_ms: float,
        request_id: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        self.model = model
        self.provider = provider
        self.latency_ms = latency_ms
        self.request_id = request_id
        self.raw = raw or {}


class LLMResponse:
    def __init__(
        self,
        content: str,
        usage: LLMUsage,
        metadata: LLMMetadata,
    ):
        self.content = content
        self.usage = usage
        self.metadata = metadata

class LLMStreamChunk:
    def __init__(self, delta: str):
        self.delta = delta


class LLMStreamResponse:
    def __init__(
        self,
        stream: Iterator[LLMStreamChunk],
        usage: Optional[LLMUsage] = None,
        metadata: Optional[LLMMetadata] = None,
    ):
        self.stream = stream
        self.usage = usage
        self.metadata = metadata
