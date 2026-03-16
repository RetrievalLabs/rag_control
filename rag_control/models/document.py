"""
Copyright (c) 2026. All rights reserved.
Licensed under the Apache License 2.0.
"""

from pydantic import BaseModel


class DocumentPolicy(BaseModel):
    top_k: int = 5
    filter_name: str | None = None
