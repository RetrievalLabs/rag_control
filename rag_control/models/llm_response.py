class LLMResponse:
    def __init__(self, content, tokens_used, model, latency):
        self.content = content
        self.tokens_used = tokens_used
        self.model = model
        self.latency = latency