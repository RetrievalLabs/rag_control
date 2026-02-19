
from dataclasses import dataclass
from typing import Any


@dataclass
class UserContext:
    user_id: str
    org_id: str
    attributes: dict[str, Any]
