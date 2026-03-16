"""
Copyright (c) 2026. All rights reserved.
Licensed under the Apache License 2.0.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class UserContext(BaseModel):
    # Keep model extensible for runtime metadata such as session/request ids.
    model_config = ConfigDict(extra="allow")

    user_id: str
    org_id: str

    attributes: dict[str, Any]
