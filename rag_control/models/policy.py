from dataclasses import dataclass
from typing import Literal

@dataclass
class GenerationPolicy:
    reasoning_level: Literal["none", "limited", "full"] = "limited"
    allow_external_knowledge: bool = False
    require_citations: bool = True
    fallback: Literal["strict", "soft"] = "strict"
    temperature: float = 0.0

@dataclass
class LoggingPolicy:
    level: Literal["minimal", "full", "forensic"] = "full"


@dataclass
class EnforcementPolicy:
    validate_citations: bool = True
    block_on_missing_citations: bool = True
    enforce_strict_fallback: bool = True
    prevent_external_knowledge: bool = True
    max_output_tokens: int | None = None

@dataclass
class Policy:
    name: str
    description: str | None = None
    generation: GenerationPolicy
    logging: LoggingPolicy
    enforcement: EnforcementPolicy