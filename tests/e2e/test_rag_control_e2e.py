from rag_control.core.engine import RAGControl
from tests.utils.fake_llm import FakeLLM


def test_rag_control_run_returns_llm_response() -> None:
    llm = FakeLLM()
    llm.enqueue_response(
        content="approved answer",
        model="fake-gpt",
        provider="fake-provider",
        latency_ms=10.0,
        request_id="req-001",
    )
    engine = RAGControl(llm=llm)

    response = engine.run("what is policy status?")

    assert response.content == "approved answer"
    assert response.metadata.model == "fake-gpt"
    assert response.metadata.provider == "fake-provider"
    assert response.metadata.latency_ms == 10.0
    assert response.metadata.request_id == "req-001"
    assert response.usage.total_tokens >= response.usage.prompt_tokens
    assert response.usage.total_tokens >= response.usage.completion_tokens
    assert llm.prompts == ["what is policy status?"]
    assert llm.generate_calls == 1
    assert llm.stream_calls == 0
