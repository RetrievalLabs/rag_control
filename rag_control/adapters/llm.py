from abc import ABC, abstractmethod

from rag_control.models.llm import LLMResponse, LLMStreamResponse

ChatMessage = dict[str, str]
PromptInput = str | list[ChatMessage]


class LLM(ABC):
    @abstractmethod
    def generate(self, prompt: PromptInput) -> LLMResponse:
        """
        Synchronous generation.
        Must return structured metadata.
        """
        pass

    @abstractmethod
    def stream(self, prompt: PromptInput) -> LLMStreamResponse:
        """
        Streaming generation.
        Must yield chunks safely.
        """
        pass
