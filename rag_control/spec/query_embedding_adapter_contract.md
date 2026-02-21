Query Embedding Adapter Contract

Version: v2026.1
Status: Draft
Applies To: All implementations of `rag_control.adapters.query_embedding.QueryEmbedding`

Purpose
- Define the required behavior for any class implementing `rag_control.adapters.query_embedding.QueryEmbedding`.
- Ensure all providers return a consistent embedding shape for retrieval and ranking workflows.

Scope
- Applies to:
  - `QueryEmbedding.embedding_model -> str`
  - `QueryEmbedding.embed(query: str, user_context: UserContext | None = None) -> QueryEmbeddingResponse`
- Output models are defined in `rag_control/models/query_embedding.py`.

Normative Terms
- MUST: required.
- SHOULD: recommended unless provider constraints prevent it.
- MAY: optional.

Embedding Model Contract
- `embedding_model` MUST be implemented as a property returning a non-empty `str`.
- Returned value MUST be stable for a given adapter instance.
- Returned value MUST identify the canonical embedding model used to produce query vectors.
- Returned value MUST match the vector store adapter's `embedding_model` for the same engine instance.

Embed Contract
- Input:
  - `query` MUST be a `str`.
  - `user_context` MAY be provided to support user-aware embedding behavior.
  - Empty query handling is provider-defined, but adapter SHOULD fail fast with a clear exception when invalid.
- Output:
  - MUST return `QueryEmbeddingResponse`.
  - `QueryEmbeddingResponse.embedding` MUST be a `list[float]`.
  - `embedding` SHOULD be non-empty for valid provider outputs.
  - Every item in `embedding` MUST be numeric and convertible to `float`.
  - `QueryEmbeddingResponse.metadata` MUST be present and include:
    - `model` (non-empty `str`)
    - `provider` (non-empty `str`)
    - `latency_ms` (`float` or numeric >= 0)
    - `dimensions` (`int` >= 0)
  - `metadata.dimensions` MUST equal `len(embedding)`.
  - `metadata.request_id` MAY be `None` when not exposed by provider.
  - `metadata.timestamp` MAY be `None` when request time is unavailable.
  - `metadata.raw` MUST be a dict and MUST NOT be shared across responses.

Error Contract
- Adapter MUST raise exceptions for transport/provider failures.
- Transport/provider failures SHOULD be raised as `QueryEmbeddingAdapterError`
  (or a subclass) from `rag_control.adapters.exceptions`.
- Exceptions SHOULD preserve actionable context (provider name, request id if available, and root cause message).
- Adapter SHOULD raise `TypeError` or `ValueError` for invalid input and malformed provider payloads.
- Adapter MUST NOT silently coerce structurally invalid embeddings (for example non-numeric vectors).

Determinism and Safety
- Adapter MUST NOT mutate returned objects after completion.
- `metadata.raw` SHOULD contain provider-native fields useful for observability.
- If present, `metadata.timestamp` SHOULD be UTC and consistently typed across adapter outputs.
- Adapter MUST avoid leaking secrets in `metadata.raw`.

Test Contract (Minimum)
- `embed`:
  - Returns `QueryEmbeddingResponse` with populated `embedding` and `metadata`.
  - Returned vector is numeric and `metadata.dimensions == len(embedding)`.
  - Propagates provider exceptions.
- Metadata:
  - `model`, `provider`, `latency_ms`, `dimensions` are set.
  - `request_id` and `timestamp` are correctly populated or `None`.
  - `raw` is a per-instance dict.

Reference Interfaces
- Adapter interface: `rag_control/adapters/query_embedding.py`
- Adapter exceptions: `rag_control/adapters/exceptions.py`
- Models: `rag_control/models/query_embedding.py`
