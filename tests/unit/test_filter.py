"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.filter.filter import FilterRegistry
from rag_control.models.config import ControlPlaneConfig


def test_filter_get_with_multiple_conditions(fake_config: ControlPlaneConfig) -> None:
    registry = FilterRegistry(fake_config)
    test_cases = [
        ("known_name_returns_filter", "default_filter", "default_filter"),
        ("unknown_name_returns_none", "missing_filter", None),
        ("none_name_returns_none", None, None),
    ]

    for case_name, filter_name, expected_name in test_cases:
        model = registry.get(filter_name)
        if expected_name is None:
            assert model is None, case_name
            continue

        assert model is not None, case_name
        assert model.name == expected_name, case_name
