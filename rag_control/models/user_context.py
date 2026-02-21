"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class UserContext(BaseModel):
    # Keep model extensible for runtime metadata such as session/request ids.
    model_config = ConfigDict(extra="allow")

    user_id: str
    org_id: str

    attributes: dict[str, Any]
