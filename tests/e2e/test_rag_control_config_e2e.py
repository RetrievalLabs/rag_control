"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pathlib import Path

import pytest
import yaml

from rag_control.core.engine import RAGControl
from rag_control.exceptions import ControlPlaneConfigValidationError
from rag_control.models.config import ControlPlaneConfig
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


def test_rag_control_config_inputs_with_multiple_conditions(
    tmp_path: Path, fake_config: ControlPlaneConfig
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(fake_config.model_dump(mode="python")),
        encoding="utf-8",
    )

    test_cases = [
        {
            "name": "valid_config_object",
            "kwargs": {"config": fake_config},
            "expected_error": None,
        },
        {
            "name": "valid_config_path",
            "kwargs": {"config_path": config_path},
            "expected_error": None,
        },
        {
            "name": "missing_config_and_path",
            "kwargs": {},
            "expected_error": "provide one of 'config' or 'config_path'",
        },
        {
            "name": "both_config_and_path_provided",
            "kwargs": {"config": fake_config, "config_path": config_path},
            "expected_error": "provide either 'config' or 'config_path', not both",
        },
        {
            "name": "invalid_inline_config_payload",
            "kwargs": {"config": {}},
            "expected_error": "invalid control plane config",
        },
    ]

    for case in test_cases:
        llm = FakeLLM()
        query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
        vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")

        if case["expected_error"] is None:
            engine = RAGControl(
                llm=llm,
                query_embedding=query_embedding,
                vector_store=vector_store,
                **case["kwargs"],
            )
            assert isinstance(engine.config, ControlPlaneConfig), case["name"]
            continue

        with pytest.raises(ControlPlaneConfigValidationError, match=case["expected_error"]):
            RAGControl(
                llm=llm,
                query_embedding=query_embedding,
                vector_store=vector_store,
                **case["kwargs"],
            )
