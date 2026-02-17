from ..models.llm_response import LLMResponse

class LLM:
    def generate(self, prompt: str) -> LLMResponse:
        raise NotImplementedError
