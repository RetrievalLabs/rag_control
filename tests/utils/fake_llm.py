"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from rag_control.adapters.llm import LLM
from rag_control.models.llm import (
    LLMMetadata,
    LLMResponse,
    LLMStreamChunk,
    LLMStreamResponse,
    LLMUsage,
)


@dataclass(slots=True)
class _PlannedOutput:
    content: str
    model: str
    provider: str
    latency_ms: float
    request_id: str | None = None
    timestamp: datetime | None = None
    temperature: float | None = None
    top_p: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    stream_chunks: tuple[str, ...] | None = None


class FakeLLM(LLM):
    """Deterministic, in-memory LLM adapter for tests."""

    def __init__(
        self,
        *,
        default_content: str = "ok",
        model: str = "fake-model",
        provider: str = "fake-provider",
        latency_ms: float = 0.0,
    ) -> None:
        self.default_content = default_content
        self.default_model = model
        self.default_provider = provider
        self.default_latency_ms = latency_ms

        self.prompts: list[Any] = []
        self.generate_calls = 0
        self.stream_calls = 0

        self._planned_outputs: list[_PlannedOutput] = []
        self._next_error: Exception | None = None

    def enqueue_response(
        self,
        *,
        content: str,
        model: str | None = None,
        provider: str | None = None,
        latency_ms: float | None = None,
        request_id: str | None = None,
        timestamp: datetime | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        stream_chunks: tuple[str, ...] | None = None,
    ) -> None:
        self._planned_outputs.append(
            _PlannedOutput(
                content=content,
                model=model or self.default_model,
                provider=provider or self.default_provider,
                latency_ms=self.default_latency_ms if latency_ms is None else latency_ms,
                request_id=request_id,
                timestamp=timestamp,
                temperature=temperature,
                top_p=top_p,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                stream_chunks=stream_chunks,
            )
        )

    def fail_next(self, error: Exception) -> None:
        self._next_error = error

    def generate(self, prompt: Any) -> LLMResponse:
        if self._next_error is not None:
            error = self._next_error
            self._next_error = None
            raise error

        self._validate_prompt(prompt)
        self.prompts.append(prompt)
        self.generate_calls += 1

        planned = self._next_planned_output()
        usage = self._usage_for(prompt=prompt, content=planned.content, planned=planned)
        metadata = self._metadata_for(planned)
        return LLMResponse(content=planned.content, usage=usage, metadata=metadata)

    def stream(self, prompt: Any) -> LLMStreamResponse:
        if self._next_error is not None:
            error = self._next_error
            self._next_error = None
            raise error

        self._validate_prompt(prompt)
        self.prompts.append(prompt)
        self.stream_calls += 1

        planned = self._next_planned_output()
        usage = self._usage_for(prompt=prompt, content=planned.content, planned=planned)
        metadata = self._metadata_for(planned)
        chunks = planned.stream_chunks or (planned.content,)

        def _iter() -> Iterator[LLMStreamChunk]:
            for delta in chunks:
                yield LLMStreamChunk(delta=delta)

        return LLMStreamResponse(stream=_iter(), usage=usage, metadata=metadata)

    def _next_planned_output(self) -> _PlannedOutput:
        if self._planned_outputs:
            return self._planned_outputs.pop(0)
        return _PlannedOutput(
            content=self.default_content,
            model=self.default_model,
            provider=self.default_provider,
            latency_ms=self.default_latency_ms,
        )

    @staticmethod
    def _validate_prompt(prompt: Any) -> None:
        if isinstance(prompt, str):
            return
        if isinstance(prompt, list):
            for message in prompt:
                if not isinstance(message, dict):
                    raise TypeError("prompt list entries must be dict messages")
                if not isinstance(message.get("role"), str):
                    raise TypeError("prompt message role must be a str")
                if not isinstance(message.get("content"), str):
                    raise TypeError("prompt message content must be a str")
            return
        raise TypeError("prompt must be a str or a list of chat messages")

    @staticmethod
    def _usage_for(prompt: Any, content: str, planned: _PlannedOutput) -> LLMUsage:
        prompt_text = FakeLLM._prompt_to_text(prompt)
        prompt_tokens = (
            planned.prompt_tokens if planned.prompt_tokens is not None else len(prompt_text.split())
        )
        completion_tokens = (
            planned.completion_tokens
            if planned.completion_tokens is not None
            else len(content.split())
        )
        total_tokens = prompt_tokens + completion_tokens
        return LLMUsage(
            prompt_tokens=max(0, prompt_tokens),
            completion_tokens=max(0, completion_tokens),
            total_tokens=max(0, total_tokens),
        )

    @staticmethod
    def _prompt_to_text(prompt: Any) -> str:
        if isinstance(prompt, str):
            return prompt
        if isinstance(prompt, list):
            return " ".join(
                message["content"]
                for message in prompt
                if isinstance(message, dict) and isinstance(message.get("content"), str)
            )
        return ""

    @staticmethod
    def _metadata_for(planned: _PlannedOutput) -> LLMMetadata:
        return LLMMetadata(
            model=planned.model,
            provider=planned.provider,
            latency_ms=max(0.0, float(planned.latency_ms)),
            request_id=planned.request_id,
            timestamp=planned.timestamp,
            temperature=planned.temperature,
            top_p=planned.top_p,
            raw={},
        )
