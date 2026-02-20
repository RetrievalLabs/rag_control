"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

import pytest

from rag_control.core.engine import RAGControl
from rag_control.exceptions import EmbeddingModelMismatchError
from rag_control.models.config import ControlPlaneConfig
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


def test_rag_control_fails_when_embedding_models_do_not_match(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v2")

    with pytest.raises(
        EmbeddingModelMismatchError, match="must match vector store embedding model"
    ):
        RAGControl(
            llm=llm,
            query_embedding=query_embedding,
            vector_store=vector_store,
            config=fake_config,
        )
