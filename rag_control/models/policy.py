from dataclasses import dataclass
from typing import Literal

@dataclass
class GenerationPolicy:
    reasoning_level: Literal["none", "limited", "full"]
    allow_external_knowledge: bool
    require_citations: bool
    fallback: Literal["strict", "soft"]
    temperature: float

@dataclass
class LoggingPolicy:
    level: Literal["minimal", "full", "forensic"]

@dataclass
class EnforcementPolicy:
    validate_citations: bool
    block_on_missing_citations: bool
    enforce_strict_fallback: bool
    prevent_external_knowledge: bool
    max_output_tokens: int | None = None

@dataclass
class Policy:
    name: str
    description: str | None = None
    generation: GenerationPolicy
    logging: LoggingPolicy
    enforcement: EnforcementPolicy