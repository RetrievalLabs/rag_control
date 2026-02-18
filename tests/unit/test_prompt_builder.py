from rag_control.core.prompt import RAGPromptBuilder
from rag_control.models.vector_store import VectorStoreRecord


def test_build_returns_expected_message_layers() -> None:
    builder = RAGPromptBuilder()
    messages = builder.build(
        query="What is the policy status?",
        retrieved_docs=[
            VectorStoreRecord(
                id="doc-001",
                content="Policy status is approved.",
                score=0.98,
                metadata={"source": "kb"},
            ),
        ],
    )

    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert messages[2]["role"] == "user"

    assert "Authority Order" in messages[0]["content"]
    assert "DEVELOPER POLICY" in messages[1]["content"]
    assert "UNTRUSTED RETRIEVED CONTEXT" in messages[2]["content"]
    assert "USER QUESTION:\nWhat is the policy status?" in messages[2]["content"]


def test_build_formats_multiple_docs_with_numbering_and_strip() -> None:
    builder = RAGPromptBuilder()
    messages = builder.build(
        query="Summarize findings",
        retrieved_docs=[
            VectorStoreRecord(
                id="doc-a",
                content="  First finding.  ",
                score=0.91,
                metadata={},
            ),
            VectorStoreRecord(
                id="doc-b",
                content="\nSecond finding.\n",
                score=0.89,
                metadata={},
            ),
        ],
    )

    user_content = messages[2]["content"]
    assert "[DOC 1]\nFirst finding." in user_content
    assert "[DOC 2]\nSecond finding." in user_content


def test_build_uses_no_documents_placeholder_when_context_empty() -> None:
    builder = RAGPromptBuilder()
    messages = builder.build(query="Any updates?", retrieved_docs=[])

    assert "[NO DOCUMENTS RETRIEVED]" in messages[2]["content"]
    assert "USER QUESTION:\nAny updates?" in messages[2]["content"]
