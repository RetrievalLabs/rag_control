"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pydantic import BaseModel


class DocumentPolicy(BaseModel):
    top_k: int = 5
    filter_name: str | None = None
