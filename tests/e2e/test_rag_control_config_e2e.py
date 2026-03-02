"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pathlib import Path
from typing import Any, TypedDict, cast

import pytest

from rag_control.core.engine import RAGControl
from rag_control.exceptions import ControlPlaneConfigValidationError
from rag_control.filter.filter import FilterRegistry
from rag_control.governance.gov import GovernanceRegistry
from rag_control.models.config import ControlPlaneConfig
from rag_control.policy.policy import PolicyRegistry
from rag_control.prompt.prompt import RAGPromptBuilder
from tests.utils.fake_llm import FakeLLM
from tests.utils.fake_query_embedding import FakeQueryEmbedding
from tests.utils.fake_vector_store import FakeVectorStore


class _ConfigInitCase(TypedDict):
    name: str
    config: ControlPlaneConfig | dict[str, object] | None
    config_path: Path | None
    expected_error: str | None


def test_rag_control_config_inputs_with_multiple_conditions(
    tmp_path: Path, fake_config: ControlPlaneConfig
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        fake_config.model_dump_json(indent=2),
        encoding="utf-8",
    )

    test_cases: list[_ConfigInitCase] = [
        {
            "name": "valid_config_object",
            "config": fake_config,
            "config_path": None,
            "expected_error": None,
        },
        {
            "name": "valid_config_path",
            "config": None,
            "config_path": config_path,
            "expected_error": None,
        },
        {
            "name": "missing_config_and_path",
            "config": None,
            "config_path": None,
            "expected_error": "provide one of 'config' or 'config_path'",
        },
        {
            "name": "both_config_and_path_provided",
            "config": fake_config,
            "config_path": config_path,
            "expected_error": "provide either 'config' or 'config_path', not both",
        },
        {
            "name": "invalid_inline_config_payload",
            "config": {},
            "config_path": None,
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
                config=cast(Any, case["config"]),
                config_path=case["config_path"],
            )
            assert isinstance(engine.config, ControlPlaneConfig), case["name"]
            continue

        assert case["expected_error"] is not None
        with pytest.raises(ControlPlaneConfigValidationError, match=case["expected_error"]):
            RAGControl(
                llm=llm,
                query_embedding=query_embedding,
                vector_store=vector_store,
                config=cast(Any, case["config"]),
                config_path=case["config_path"],
            )


def test_rag_control_init_assigns_dependencies_and_registries(
    fake_config: ControlPlaneConfig,
) -> None:
    llm = FakeLLM()
    query_embedding = FakeQueryEmbedding(model="fake-embedding-v1")
    vector_store = FakeVectorStore(embedding_model="fake-embedding-v1")

    engine = RAGControl(
        llm=llm,
        query_embedding=query_embedding,
        vector_store=vector_store,
        config=fake_config,
    )

    assert engine.llm is llm
    assert engine.query_embedding is query_embedding
    assert engine.vector_store is vector_store
    assert isinstance(engine.policy_registry, PolicyRegistry)
    assert isinstance(engine.governance_registry, GovernanceRegistry)
    assert isinstance(engine.filter_registry, FilterRegistry)
    assert isinstance(engine.prompt_builder, RAGPromptBuilder)
