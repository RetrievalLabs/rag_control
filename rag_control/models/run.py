"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pydantic import BaseModel

from .llm import LLMResponse, LLMStreamResponse


class RunResponse(BaseModel):
    policy_name: str
    org_id: str
    user_id: str
    trace_id: str | None = None
    filter_name: str | None = None
    retrieval_top_k: int
    retrieved_count: int
    enforcement_passed: bool
    response: LLMResponse


class StreamResponse(BaseModel):
    policy_name: str
    org_id: str
    user_id: str
    trace_id: str | None = None
    filter_name: str | None = None
    retrieval_top_k: int
    retrieved_count: int
    enforcement_attached: bool
    response: LLMStreamResponse
