import pytest

from rag_control.core.engine import RAGControl
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


def test_rag_control_fails_when_embedding_models_do_not_match() -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v2")

    with pytest.raises(ValueError, match="must match vector store embedding model"):
        RAGControl(llm=llm, query_embedding=query_embedding, vector_store=vector_store)


def test_rag_control_fails_when_runtime_embedding_response_model_does_not_match() -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")
    engine = RAGControl(llm=llm, query_embedding=query_embedding, vector_store=vector_store)

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v2",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-002",
    )

    with pytest.raises(ValueError, match="must match vector store embedding model"):
        engine.run("what is policy status?")
