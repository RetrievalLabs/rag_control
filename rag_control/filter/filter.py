"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.models.config import ControlPlaneConfig
from rag_control.models.filter import Filter as FilterModel


class FilterRegistry:
    def __init__(self, config: ControlPlaneConfig):
        self.filter_map: dict[str, FilterModel] = {
            filter_model.name: filter_model for filter_model in config.filters
        }

    # Returns the FilterModel for the given name, or None if not found.
    def get(self, name: str) -> FilterModel | None:
        if name is None:
            return None
        return self.filter_map.get(name)
