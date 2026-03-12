"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from typing import Literal

from pydantic import BaseModel, Field
from .document import DocumentPolicy


class GenerationPolicy(BaseModel):
    reasoning_level: Literal["none", "limited", "full"] = "limited"
    allow_external_knowledge: bool = False
    require_citations: bool = True
    fallback: Literal["strict", "soft"] = "strict"
    temperature: float = 0.0


class LoggingPolicy(BaseModel):
    level: Literal["minimal", "full"] = "full"


class EnforcementPolicy(BaseModel):
    validate_citations: bool = True
    block_on_missing_citations: bool = True
    enforce_strict_fallback: bool = True
    prevent_external_knowledge: bool = True
    max_output_tokens: int | None = None


class Policy(BaseModel):
    name: str
    description: str | None = None
    generation: GenerationPolicy
    logging: LoggingPolicy
    enforcement: EnforcementPolicy
    document_policy: DocumentPolicy = Field(default_factory=DocumentPolicy)

    
