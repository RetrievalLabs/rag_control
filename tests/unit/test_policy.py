"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import TypedDict

import pytest
from pydantic import ValidationError

from rag_control.models.config import ControlPlaneConfig
from rag_control.models.policy import (
    DocumentPolicy,
    EnforcementPolicy,
    GenerationPolicy,
    LoggingPolicy,
)
from rag_control.models.policy import (
    Policy as PolicyModel,
)
from rag_control.policy.policy import PolicyRegistry


class _PolicyLookupCase(TypedDict):
    name: str
    policy_name: str
    expect_found: bool
    expected_description: str | None


def test_policy_get_with_multiple_conditions(fake_config: ControlPlaneConfig) -> None:
    research_policy = PolicyModel(
        name="research_policy",
        description="Research policy for exploratory use cases.",
        generation=GenerationPolicy(reasoning_level="full", fallback="soft"),
        logging=LoggingPolicy(level="forensic"),
        enforcement=EnforcementPolicy(block_on_missing_citations=False),
        document_policy=DocumentPolicy(top_k=8),
    )

    config = fake_config.model_copy(update={"policies": [*fake_config.policies, research_policy]})
    policy_registry = PolicyRegistry(config)

    test_cases: list[_PolicyLookupCase] = [
        {
            "name": "default_policy_exists",
            "policy_name": "default_policy",
            "expect_found": True,
            "expected_description": "Default policy for tests.",
        },
        {
            "name": "additional_policy_exists",
            "policy_name": "research_policy",
            "expect_found": True,
            "expected_description": "Research policy for exploratory use cases.",
        },
        {
            "name": "missing_policy_returns_none",
            "policy_name": "unknown_policy",
            "expect_found": False,
            "expected_description": None,
        },
    ]

    for case in test_cases:
        result = policy_registry.get(case["policy_name"])
        if case["expect_found"]:
            assert result is not None, case["name"]
            assert result.name == case["policy_name"], case["name"]
            assert result.description == case["expected_description"], case["name"]
            if case["policy_name"] == "research_policy":
                assert result.document_policy.top_k == 8, case["name"]
            continue

        assert result is None, case["name"]


@pytest.mark.parametrize(
    ("document_policy", "expected_error"),
    [
        (
            DocumentPolicy(top_k=0),
            "document_policy.top_k must be greater than 0",
        ),
    ],
)
def test_document_policy_validation_errors(
    fake_config: ControlPlaneConfig,
    document_policy: DocumentPolicy,
    expected_error: str,
) -> None:
    invalid_policy = PolicyModel(
        name="invalid_document_policy",
        generation=GenerationPolicy(),
        logging=LoggingPolicy(),
        enforcement=EnforcementPolicy(),
        document_policy=document_policy,
    )

    with pytest.raises(ValidationError, match=expected_error):
        dumped_config = fake_config.model_dump()
        dumped_config["policies"].append(invalid_policy.model_dump())
        ControlPlaneConfig.model_validate(dumped_config)
