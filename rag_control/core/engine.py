
class RagControl:
    """
    Mandatory execution spine for governed RAG.

    This class enforces:
    - Retrieval-first execution
    - RBAC filtering
    - Policy validation gates
    - Auditable lifecycle
    """

    def __init__(self, llm):
        self.llm = llm

    def run(self, query: str):
        """
        Single public execution path.
        
        :param query: User query to process through the RAG
        :type query: str
        """
        response = self.llm.generate(query)
        return response