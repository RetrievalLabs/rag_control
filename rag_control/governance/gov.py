"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.models.config import ControlPlaneConfig
from rag_control.models.org import OrgConfig


class GovernanceRegistry:
    def __init__(self, config: ControlPlaneConfig):
        self.org_map: dict[str, OrgConfig] = {
            org.org_id: org.model_copy(
                update={
                    "policy_rules": sorted(
                        org.policy_rules,
                        key=lambda policy_rule: policy_rule.priority,
                        reverse=True,
                    )
                }
            )
            for org in config.orgs
        }

    def get_org(self, org_name: str) -> OrgConfig | None:
        return self.org_map.get(org_name)
