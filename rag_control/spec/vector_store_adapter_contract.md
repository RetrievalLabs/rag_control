Vector Store Adapter Contract

Version: v2026.1
Status: Draft
Applies To: All implementations of `rag_control.adapters.vector_store.VectorStore`

Purpose
- Define the required behavior for any class implementing `rag_control.adapters.vector_store.VectorStore`.
- Ensure providers return a consistent retrieval shape for downstream ranking and generation.

Scope
- Applies to:
  - `VectorStore.embedding_model -> str`
  - `VectorStore.search(embedding: list[float], top_k: int = 5, user_context: UserContext | None = None, filter: Filter | None = None) -> VectorStoreSearchResponse`
- Output models are defined in `rag_control/models/vector_store.py`.

Normative Terms
- MUST: required.
- SHOULD: recommended unless provider constraints prevent it.
- MAY: optional.

Embedding Model Contract
- `embedding_model` MUST be implemented as a property returning a non-empty `str`.
- Returned value MUST be stable for a given adapter instance.
- Returned value MUST identify the canonical embedding model expected by the index.
- Returned value MUST match the query embedding adapter's `embedding_model` for the same engine instance.

Search Contract
- Input:
  - `embedding` MUST be a `list[float]`.
  - `embedding` SHOULD be non-empty for valid retrieval requests.
  - `top_k` MUST be an integer >= 1.
  - `user_context` MAY be provided to support user-scoped retrieval.
  - `filter` MAY be provided to support metadata-constrained retrieval.
- Output:
  - MUST return `VectorStoreSearchResponse`.
  - `VectorStoreSearchResponse.records` MUST be a list of `VectorStoreRecord`.
  - Every `VectorStoreRecord` MUST include:
    - `id` (non-empty `str`)
    - `content` (`str`, empty allowed)
    - `score` (numeric `float`)
    - `metadata` (dict)
  - `VectorStoreSearchResponse.metadata` MUST include:
    - `provider` (non-empty `str`)
    - `index` (non-empty `str`)
    - `latency_ms` (`float` or numeric >= 0)
    - `top_k` (`int` >= 1)
    - `returned` (`int` >= 0)
  - `metadata.returned` MUST equal `len(records)`.
  - `metadata.request_id` MAY be `None`.
  - `metadata.timestamp` MAY be `None`.
  - `metadata.raw` MUST be a dict and MUST NOT be shared across responses.

Error Contract
- Adapter MUST raise exceptions for transport/provider failures.
- Adapter SHOULD raise `TypeError` or `ValueError` for invalid input and malformed payloads.
- Adapter MUST NOT silently coerce structurally invalid records.

Determinism and Safety
- Adapter MUST NOT mutate returned objects after completion.
- `metadata.raw` SHOULD contain provider-native fields useful for observability.
- Adapter MUST avoid leaking secrets in `metadata.raw`.

Test Contract (Minimum)
- `search`:
  - Returns `VectorStoreSearchResponse` with records and metadata.
  - `metadata.returned == len(records)`.
  - Propagates provider exceptions.
- Metadata:
  - `provider`, `index`, `latency_ms`, `top_k`, `returned` are set.
  - `request_id` and `timestamp` are correctly populated or `None`.
  - `raw` is a per-instance dict.

Reference Interfaces
- Adapter interface: `rag_control/adapters/vector_store.py`
- Models: `rag_control/models/vector_store.py`
