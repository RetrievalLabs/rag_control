from rag_control.core.engine import RAGControl
from rag_control.models.vector_store import VectorStoreRecord
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


def test_rag_control_run_returns_llm_response_with_retrieval_context() -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding()
    vector_store = FakeVectorStore()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-001",
    )

    vector_store.enqueue_response(
        records=[
            VectorStoreRecord(
                id="doc-001",
                content="Policy status is approved.",
                score=0.97,
                metadata={"source": "policy-kb"},
            ),
        ],
        provider="fake-vector-provider",
        index="policy-index",
        latency_ms=4.0,
        request_id="search-001",
    )

    llm.enqueue_response(
        content="approved answer",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-001",
        prompt_tokens=12,
    )

    engine = RAGControl(llm=llm, query_embedding=query_embedding, vector_store=vector_store)
    llm_response = engine.run("what is policy status?")

    assert llm_response.content == "approved answer"
    assert llm_response.metadata.model == "fake-gpt"
    assert llm_response.metadata.provider == "fake-provider"
    assert llm_response.metadata.latency_ms == 10.0
    assert llm_response.metadata.request_id == "req-001"
    assert llm_response.usage.total_tokens >= llm_response.usage.prompt_tokens
    assert llm_response.usage.total_tokens >= llm_response.usage.completion_tokens

    assert isinstance(llm.prompts[0], list)
    assert llm.prompts[0][-1]["role"] == "user"
    assert "what is policy status?" in llm.prompts[0][-1]["content"]
    assert query_embedding.queries == ["what is policy status?"]
    assert vector_store.embeddings == [[0.11, 0.22, 0.33]]
    assert vector_store.search_calls == 1
    assert llm.generate_calls == 1
    assert llm.stream_calls == 0
    assert query_embedding.embed_calls == 1
