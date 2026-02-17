
class RagControl:

    def __init__(self, llm):
        self.llm = llm

    def run(self, query: str):
        response = self.llm.generate(query)
        return response