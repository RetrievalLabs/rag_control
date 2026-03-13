"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

import pytest

from rag_control.models.config import ControlPlaneConfig
from rag_control.models.filter import FilterCondition
from rag_control.models.filter import Filter
from rag_control.models.org import OrgConfig
from rag_control.models.document import DocumentPolicy
from rag_control.models.policy import (
    EnforcementPolicy,
    GenerationPolicy,
    LoggingPolicy,
    Policy,
)
from rag_control.models.deny_rule import DenyRule, DenyRuleCondition, DenyRuleLogicalCondition
from rag_control.models.policy_rule import (
    PolicyRule,
    PolicyRuleCondition,
    PolicyRuleLogicalCondition,
)


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
                document_policy=DocumentPolicy(filter_name="default_filter", top_k=5),
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
                        name="apply_default",
                        description="Apply default policy.",
                        priority=1,
                        apply_policy="default_policy",
                        when=PolicyRuleLogicalCondition(
                            all=[
                                PolicyRuleCondition(
                                    field="org_tier",
                                    operator="equals",
                                    value="enterprise",
                                )
                            ]
                        ),
                    )
                ],
                deny_rules=[
                    DenyRule(
                        name="deny_free_tier",
                        description="Deny free tier users.",
                        priority=1,
                        effect="deny",
                        when=DenyRuleLogicalCondition(
                            all=[
                                DenyRuleCondition(
                                    field="org_tier",
                                    operator="equals",
                                    value="free",
                                    source="user",
                                )
                            ]
                        ),
                    )
                ],
            )
        ],
    )
