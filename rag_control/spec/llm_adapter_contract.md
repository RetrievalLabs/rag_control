LLM Adapter Contract

Version: v2026.1
Status: Draft
Applies To: All implementations of `rag_control.adapters.llm.LLM`

Purpose
- Define the required behavior for any class implementing `rag_control.adapters.llm.LLM`.
- Ensure all providers return a consistent shape for engine-level orchestration.

Scope
- Applies to:
  - `LLM.generate(prompt: str) -> LLMResponse`
  - `LLM.stream(prompt: str) -> LLMStreamResponse`
- Output models are defined in `rag_control/models/llm.py`.

Normative Terms
- MUST: required.
- SHOULD: recommended unless provider constraints prevent it.
- MAY: optional.

Generate Contract
- Input:
  - `prompt` MUST be a `str`.
  - Empty prompt handling is provider-defined, but adapter SHOULD fail fast with a clear exception when invalid.
- Output:
  - MUST return `LLMResponse`.
  - `LLMResponse.content` MUST be a `str` (empty string allowed).
  - `LLMResponse.usage` MUST be present and contain non-negative integers:
    - `prompt_tokens`
    - `completion_tokens`
    - `total_tokens`
  - `LLMResponse.metadata` MUST be present and include:
    - `model` (non-empty `str`)
    - `provider` (non-empty `str`)
    - `latency_ms` (`float` or numeric >= 0)
  - `metadata.request_id` MAY be `None` when not exposed by provider.
  - `metadata.raw` MUST be a dict and MUST NOT be shared across responses.

Stream Contract
- Input:
  - `prompt` MUST be a `str`.
- Output:
  - MUST return `LLMStreamResponse`.
  - `LLMStreamResponse.stream` MUST be an iterator yielding `LLMStreamChunk`.
  - Every yielded `LLMStreamChunk.delta` MUST be a `str` (empty string allowed).
  - Chunks MUST preserve provider order.
  - Adapter SHOULD avoid emitting `None` or non-text payloads as chunk deltas.
- Metadata/Usage:
  - `LLMStreamResponse.metadata` SHOULD be populated when known.
  - `LLMStreamResponse.usage` MAY be `None` until final usage is known.
  - If provider exposes final usage only at completion, adapter SHOULD publish usage only when complete.
  - If provider never exposes usage, adapter MAY leave `usage=None`.

Error Contract
- Adapter MUST raise exceptions for transport/provider failures.
- Exceptions SHOULD preserve actionable context (provider name, request id if available, and root cause message).
- Adapter MUST NOT silently swallow stream errors.
- On stream failure, partial chunks already yielded MAY be retained by caller; adapter SHOULD fail on next iteration with a clear exception.

Determinism and Safety
- Adapter MUST NOT mutate returned objects after completion, except:
  - Streaming usage/metadata MAY transition from `None` to populated state during lifecycle if implementation documents this behavior.
- `metadata.raw` SHOULD contain provider-native fields useful for observability.
- Adapter MUST avoid leaking secrets in `metadata.raw`.

Test Contract (Minimum)
- `generate`:
  - Returns `LLMResponse` with populated `content`, `usage`, and `metadata`.
  - Usage values are non-negative and internally consistent (`total_tokens >= prompt_tokens`, `total_tokens >= completion_tokens`).
- `stream`:
  - Returns `LLMStreamResponse` with an iterator of `LLMStreamChunk`.
  - Concatenating `chunk.delta` yields expected generated text.
  - Handles empty output stream without crashing.
  - Propagates provider exceptions.
- Metadata:
  - `model`, `provider`, `latency_ms` are set.
  - `raw` is a per-instance dict.

Reference Interfaces
- Adapter interface: `rag_control/adapters/llm.py`
- Models: `rag_control/models/llm.py`
