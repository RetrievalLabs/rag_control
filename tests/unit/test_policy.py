"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import TypedDict

from rag_control.models.config import ControlPlaneConfig
from rag_control.models.policy import (
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
            continue

        assert result is None, case["name"]
