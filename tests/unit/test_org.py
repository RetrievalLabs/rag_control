"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

import pytest
from pydantic import ValidationError

from rag_control.models.config import ControlPlaneConfig


def test_org_document_policy_top_k_validation_error(fake_config: ControlPlaneConfig) -> None:
    dumped_config = fake_config.model_dump()
    dumped_config["orgs"][0]["document_policy"] = {"top_k": 0}

    with pytest.raises(ValidationError, match="document_policy.top_k must be greater than 0"):
        ControlPlaneConfig.model_validate(dumped_config)
