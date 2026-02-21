"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from rag_control.models.user_context import UserContext


def test_user_context_allows_extra_top_level_fields() -> None:
    user_context = UserContext.model_validate(
        {
            "user_id": "u-1",
            "org_id": "org-1",
            "attributes": {"role": "analyst"},
            "session_id": "sess-123",
            "request_id": "req-abc",
        }
    )

    serialized = user_context.model_dump()
    assert serialized["session_id"] == "sess-123"
    assert serialized["request_id"] == "req-abc"
