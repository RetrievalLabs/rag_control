from ..models.llm_response import LLMResponse

class LLM:
    """
    Base class for LLM implementations. All LLMs should inherit from this class and implement the generate method.
    """
    def generate(self, prompt: str) -> LLMResponse:
        raise NotImplementedError
