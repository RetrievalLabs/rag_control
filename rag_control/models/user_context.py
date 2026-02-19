from typing import Any

from pydantic import BaseModel


class UserContext(BaseModel):
    user_id: str
    org_id: str
    attributes: dict[str, Any]
