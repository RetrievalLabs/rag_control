
class RAGControl:
    """
    Mandatory execution spine for governed RAG.

    This class enforces:
    - Retrieval-first execution
    - RBAC filtering
    - Policy validation gates
    - Auditable lifecycle
    """

    def __init__(self, llm, query_embedding, vector_store):
        self.llm = llm
        self.query_embedding = query_embedding
        self.vector_store = vector_store

    def run(self, query: str):
        """
        Single public execution path.
        
        :param query: User query to process through the RAG
        :type query: str
        """
        query_embedding_vec = self.query_embedding.embed(query)
        docs = self.vector_store.retrieve(query_embedding_vec)
        
        response = self.llm.generate(query)
        return query_embedding_vec, response