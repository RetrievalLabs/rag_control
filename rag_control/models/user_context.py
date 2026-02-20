"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import Any

from pydantic import BaseModel


class UserContext(BaseModel):
    user_id: str
    org_id: str
    attributes: dict[str, Any]
