"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

import re
from collections.abc import Iterator

from rag_control.exceptions.enforcement import EnforcementPolicyViolationError
from rag_control.models.config import ControlPlaneConfig
from rag_control.models.llm import LLMResponse, LLMStreamChunk, LLMStreamResponse
from rag_control.models.policy import Policy as PolicyModel
from rag_control.models.vector_store import VectorStoreRecord

# Extract citation indices from answer text, e.g. "[DOC 2]".
_CITATION_PATTERN = re.compile(r"\[DOC\s+(\d+)\]")
_STRICT_FALLBACK_TEXTS = {
    "I don’t have enough information in the provided context.",
    "I don't have enough information in the provided context.",
}


class PolicyRegistry:
    def __init__(self, config: ControlPlaneConfig):
        self.policy_map: dict[str, PolicyModel] = {
            policy.name: policy for policy in config.policies
        }

    # Returns the PolicyModel for the given name, or None if not found.
    def get(self, name: str) -> PolicyModel | None:
        return self.policy_map.get(name)

    def enforce_response(
        self,
        *,
        policy_name: str,
        response: LLMResponse,
        retrieved_docs: list[VectorStoreRecord],
    ) -> None:
        policy = self.get(policy_name)
        if policy is None:
            return

        # Aggregate all enforcement failures so callers get a single actionable error.
        violations: list[str] = []
        violations.extend(
            self._check_max_output_tokens(
                max_output_tokens=policy.enforcement.max_output_tokens,
                completion_tokens=response.usage.completion_tokens,
            )
        )
        violations.extend(
            self._check_response_content(
                policy=policy,
                content=response.content,
                retrieved_docs=retrieved_docs,
            )
        )
        if violations:
            raise EnforcementPolicyViolationError(policy_name, violations)

    def enforce_stream_response(
        self,
        *,
        policy_name: str,
        response: LLMStreamResponse,
        retrieved_docs: list[VectorStoreRecord],
    ) -> LLMStreamResponse:
        policy = self.get(policy_name)
        if policy is None:
            return response

        def _validated_stream() -> Iterator[LLMStreamChunk]:
            # Stream chunks through immediately, then validate once we have full content.
            collected_deltas: list[str] = []
            for chunk in response.stream:
                collected_deltas.append(chunk.delta)
                yield chunk

            violations: list[str] = []
            if response.usage is not None:
                violations.extend(
                    self._check_max_output_tokens(
                        max_output_tokens=policy.enforcement.max_output_tokens,
                        completion_tokens=response.usage.completion_tokens,
                    )
                )
            violations.extend(
                self._check_response_content(
                    policy=policy,
                    # Apply content checks against the final assembled stream output.
                    content="".join(collected_deltas),
                    retrieved_docs=retrieved_docs,
                )
            )
            if violations:
                raise EnforcementPolicyViolationError(policy_name, violations)

        return LLMStreamResponse(
            stream=_validated_stream(),
            usage=response.usage,
            metadata=response.metadata,
        )

    @staticmethod
    def _check_max_output_tokens(
        max_output_tokens: int | None,
        completion_tokens: int,
    ) -> list[str]:
        if max_output_tokens is None:
            return []
        if completion_tokens <= max_output_tokens:
            return []
        return [
            "completion tokens exceed enforcement.max_output_tokens "
            f"({completion_tokens} > {max_output_tokens})"
        ]

    @staticmethod
    def _check_response_content(
        *,
        policy: PolicyModel,
        content: str,
        retrieved_docs: list[VectorStoreRecord],
    ) -> list[str]:
        violations: list[str] = []
        citation_indexes = [int(match) for match in _CITATION_PATTERN.findall(content)]

        if policy.generation.require_citations and len(citation_indexes) == 0:
            if policy.enforcement.block_on_missing_citations:
                violations.append("missing citations while generation.require_citations=true")

        if policy.enforcement.validate_citations and citation_indexes:
            # "[DOC 1]" maps to retrieved_docs[0], so valid range is 1..len(retrieved_docs).
            max_doc_index = len(retrieved_docs)
            invalid_indexes = [idx for idx in citation_indexes if idx < 1 or idx > max_doc_index]
            if invalid_indexes:
                violations.append(f"invalid citations out of retrieved range: {invalid_indexes}")

        stripped_content = content.strip()
        if (
            policy.enforcement.prevent_external_knowledge
            and retrieved_docs
            and stripped_content
            and len(citation_indexes) == 0
        ):
            violations.append(
                "response may rely on external knowledge: citations are required "
                "when enforcement.prevent_external_knowledge=true"
            )

        if not retrieved_docs:
            # With no grounded context, strict mode must return the exact fallback response.
            should_force_strict_fallback = (
                policy.enforcement.enforce_strict_fallback
                and policy.generation.fallback == "strict"
            ) or policy.enforcement.prevent_external_knowledge
            if should_force_strict_fallback and stripped_content not in _STRICT_FALLBACK_TEXTS:
                violations.append(
                    "response must use strict fallback when no documents are retrieved"
                )

        return violations
