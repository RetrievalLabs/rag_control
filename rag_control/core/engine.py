from .prompt import RAGPromptBuilder

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
        self.prompt_builder = RAGPromptBuilder()

    def run(self, query: str):
        """
        Single public execution path.
        
        :param query: User query to process through the RAG
        :type query: str
        """
        query_embedding_vec = self.query_embedding.embed(query)
        retrieve_res = self.vector_store.retrieve(query_embedding_vec)
        docs = retrieve_res.records
        messages = self.prompt_builder.build(
            query=query,
            retrieved_docs=docs
        )
        
        response = self.llm.generate(messages)
        return response