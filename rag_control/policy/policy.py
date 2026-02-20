"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.models.config import ControlPlaneConfig
from rag_control.models.policy import Policy as PolicyModel


class Policy:
    def __init__(self, config: ControlPlaneConfig):
        self.policy_map: dict[str, PolicyModel] = {
            policy.name: policy for policy in config.policies
        }

    # Returns the PolicyModel for the given name, or None if not found.
    def get(self, name: str) -> PolicyModel | None:
        return self.policy_map.get(name)
