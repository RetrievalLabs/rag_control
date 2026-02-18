from abc import ABC, abstractmethod

from rag_control.models.llm import LLMResponse, LLMStreamResponse


class LLM(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """
        Synchronous generation.
        Must return structured metadata.
        """
        pass

    @abstractmethod
    def stream(self, prompt: str) -> LLMStreamResponse:
        """
        Streaming generation.
        Must yield chunks safely.
        """
        pass
