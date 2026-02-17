from rag_control.core.engine import RAGControl
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding


def test_rag_control_run_returns_query_embedding_and_llm_response() -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding()

    query_embedding.enqueue_response(
        embedding=[0.11, 0.22, 0.33],
        model="fake-embedding-v1",
        provider="fake-provider",
        latency_ms=3.0,
        request_id="embed-001",
    )

    llm.enqueue_response(
        content="approved answer",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-001",
    )
    engine = RAGControl(llm=llm, query_embedding=query_embedding)

    embedding_response, llm_response = engine.run("what is policy status?")

    assert embedding_response.embedding == [0.11, 0.22, 0.33]
    assert embedding_response.metadata.model == "fake-embedding-v1"
    assert embedding_response.metadata.provider == "fake-provider"
    assert embedding_response.metadata.latency_ms == 3.0
    assert embedding_response.metadata.dimensions == 3
    assert embedding_response.metadata.request_id == "embed-001"

    assert llm_response.content == "approved answer"
    assert llm_response.metadata.model == "fake-gpt"
    assert llm_response.metadata.provider == "fake-provider"
    assert llm_response.metadata.latency_ms == 10.0
    assert llm_response.metadata.request_id == "req-001"
    assert llm_response.usage.total_tokens >= llm_response.usage.prompt_tokens
    assert llm_response.usage.total_tokens >= llm_response.usage.completion_tokens

    assert llm.prompts == ["what is policy status?"]
    assert query_embedding.queries == ["what is policy status?"]
    assert llm.generate_calls == 1
    assert llm.stream_calls == 0
    assert query_embedding.embed_calls == 1
