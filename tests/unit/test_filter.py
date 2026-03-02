"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.filter.filter import FilterRegistry
from rag_control.models.config import ControlPlaneConfig


def test_filter_get_returns_filter_by_name(fake_config: ControlPlaneConfig) -> None:
    registry = FilterRegistry(fake_config)

    model = registry.get("default_filter")

    assert model is not None
    assert model.name == "default_filter"


def test_filter_get_returns_none_for_unknown_name(fake_config: ControlPlaneConfig) -> None:
    registry = FilterRegistry(fake_config)

    model = registry.get("missing_filter")

    assert model is None
