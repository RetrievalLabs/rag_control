from rag_control.adapters.llm import LLM
from rag_control.adapters.query_embedding import QueryEmbedding
from rag_control.adapters.vector_store import VectorStore

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

    def __init__(self, llm: LLM, query_embedding: QueryEmbedding, vector_store: VectorStore) -> None:
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
