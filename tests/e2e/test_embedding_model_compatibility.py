import pytest

from rag_control.core.engine import RAGControl
from rag_control.exceptions import EmbeddingModelMismatchError
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


def test_rag_control_fails_when_embedding_models_do_not_match() -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v2")

    with pytest.raises(EmbeddingModelMismatchError, match="must match vector store embedding model"):
        RAGControl(llm=llm, query_embedding=query_embedding, vector_store=vector_store)


