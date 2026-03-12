"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

import pytest

from rag_control.models.config import ControlPlaneConfig
from rag_control.models.filter import Condition as FilterCondition
from rag_control.models.filter import Filter
from rag_control.models.org import DocumentPolicy, OrgConfig
from rag_control.models.policy import (
    EnforcementPolicy,
    GenerationPolicy,
    LoggingPolicy,
    Policy,
)
from rag_control.models.access_rule import Condition, LogicalCondition, PolicyRule


@pytest.fixture
def fake_config() -> ControlPlaneConfig:
    return ControlPlaneConfig(
        policies=[
            Policy(
                name="default_policy",
                description="Default policy for tests.",
                generation=GenerationPolicy(),
                logging=LoggingPolicy(),
                enforcement=EnforcementPolicy(),
            )
        ],
        filters=[
            Filter(
                name="default_filter",
                description="Default filter for tests.",
                condition=FilterCondition(
                    field="org_tier",
                    operator="equals",
                    value="enterprise",
                    source="user",
                ),
            )
        ],
        orgs=[
            OrgConfig(
                org_id="test_org",
                description="Test organization.",
                default_policy="default_policy",
                policy_rules=[
                    PolicyRule(
                        name="allow_enterprise",
                        description="Allow enterprise traffic.",
                        priority=1,
                        effect="allow",
                        apply_policy="default_policy",
                        when=LogicalCondition(
                            all=[
                                Condition(
                                    field="org_tier",
                                    operator="equals",
                                    value="enterprise",
                                    source="user",
                                )
                            ]
                        ),
                    )
                ],
                document_policy=DocumentPolicy(filter_name="default_filter"),
            )
        ],
    )
