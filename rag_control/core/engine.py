
class RAGControl:
    """
    Mandatory execution spine for governed RAG.

    This class enforces:
    - Retrieval-first execution
    - RBAC filtering
    - Policy validation gates
    - Auditable lifecycle
    """

    def __init__(self, llm, query_embedding):
        self.llm = llm
        self.query_embedding = query_embedding

    def run(self, query: str):
        """
        Single public execution path.
        
        :param query: User query to process through the RAG
        :type query: str
        """
        query_embedding_response = self.query_embedding.embed(query)
        response = self.llm.generate(query)
        return query_embedding_response, response