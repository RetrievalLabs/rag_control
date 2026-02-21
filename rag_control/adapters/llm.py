"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from abc import ABC, abstractmethod

from rag_control.models.llm import LLMResponse, LLMStreamResponse
from rag_control.models.user_context import UserContext

ChatMessage = dict[str, str]
PromptInput = str | list[ChatMessage]


class LLM(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: PromptInput,
        temperature: float | None = None,
        user_context: UserContext | None = None,
    ) -> LLMResponse:
        """
        Synchronous generation.
        Must return structured metadata.
        """
        pass

    @abstractmethod
    def stream(
        self,
        prompt: PromptInput,
        temperature: float | None = None,
        user_context: UserContext | None = None,
    ) -> LLMStreamResponse:
        """
        Streaming generation.
        Must yield chunks safely.
        """
        pass
