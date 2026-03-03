RAG Execution Contract

Version: v2026.1
Status: Draft
Applies To:
- `rag_control.core.engine.RAGControl`
- `rag_control.models.run.RunResponse`
- `rag_control.models.run.StreamResponse`

Purpose
- Define input/output contracts for `RAGControl.run` and `RAGControl.stream`.
- Define execution-time policy/governance/enforcement behavior and failure semantics.
- Define execution-time audit emission behavior and request correlation requirements.
- Define execution-time trace emission behavior and response trace correlation.

Normative Terms
- MUST: required.
- SHOULD: recommended unless system constraints prevent it.
- MAY: optional.

Engine Interface
- `__init__(llm: LLM, query_embedding: QueryEmbedding, vector_store: VectorStore, config: ControlPlaneConfig | None = None, config_path: str | Path | None = None)`
- `run(query: str, user_context: UserContext) -> RunResponse`
- `stream(query: str, user_context: UserContext) -> StreamResponse`

Initialization Contract
- Inputs:
  - Exactly one of `config` or `config_path` MUST be provided.
  - Providing both `config` and `config_path` MUST raise `ControlPlaneConfigValidationError`.
  - Providing neither `config` nor `config_path` MUST raise `ControlPlaneConfigValidationError`.
  - `llm`, `query_embedding`, and `vector_store` MUST be provided.
- Adapter assignment:
  - Constructor MUST assign adapter instances as:
    - `self.llm = llm`
    - `self.query_embedding = query_embedding`
    - `self.vector_store = vector_store`
- Config loading:
  - If `config_path` is provided, implementation MUST load and validate config from path.
  - If `config` is provided, implementation MUST validate it as `ControlPlaneConfig`.
- Embedding compatibility:
  - Query embedding model and vector store embedding model MUST match.
  - Mismatch MUST raise `EmbeddingModelMismatchError`.
  - Non-string model identifiers MUST raise `EmbeddingModelTypeError`.
  - Empty/blank model identifiers MUST raise `EmbeddingModelValidationError`.
- Initialized runtime components:
  - `policy_registry` MUST be initialized from config policies.
  - `governance_registry` MUST be initialized from org/rule configuration.
  - `filter_registry` MUST be initialized from config filters.
  - `prompt_builder` MUST be initialized for policy-aware prompt construction.
  - `audit_logger` MUST be initialized (default or injected implementation).
  - `tracer` MUST be initialized (default or injected implementation).
- Init failure behavior:
  - Constructor MUST fail fast and raise the corresponding exception when any init validation fails.
  - No partially-initialized instance state is part of this contract.

Run Contract
- Input:
  - `query` MUST be a non-empty user question string.
  - `user_context.org_id` MUST be present and resolvable to an org in governance.
- Output:
  - MUST return `RunResponse` on success.
  - `RunResponse.response` MUST be a valid `LLMResponse`.
  - `RunResponse.enforcement_passed` MUST be `true` when returned.
  - `RunResponse.policy_name` MUST reflect the resolved policy used for generation/enforcement.
  - `RunResponse.org_id` and `RunResponse.user_id` MUST reflect request context.
  - `RunResponse.retrieval_top_k` MUST reflect org-level retrieval configuration.
  - `RunResponse.retrieved_count` MUST reflect number of retrieved records actually used.
  - `RunResponse.trace_id` MUST carry a per-request trace identifier.

Stream Contract
- Input:
  - Same validation requirements as `run`.
- Output:
  - MUST return `StreamResponse` on success.
  - `StreamResponse.response` MUST be a valid `LLMStreamResponse`.
  - `StreamResponse.enforcement_passed` MUST be `true` when returned.
  - `StreamResponse.policy_name` MUST reflect the resolved policy.
  - `StreamResponse.org_id` and `StreamResponse.user_id` MUST reflect request context.
  - `StreamResponse.retrieval_top_k` MUST reflect org-level retrieval configuration.
  - `StreamResponse.retrieved_count` MUST reflect number of retrieved records actually used.
  - `StreamResponse.trace_id` MUST carry a per-request trace identifier.

Execution Order (Normative)
- Implementations MUST execute the following stages:
  1. Validate org identity from `user_context`.
  2. Resolve org and retrieval filter.
  3. Embed query.
  4. Retrieve documents with org `document_policy.top_k`.
  5. Resolve final policy via governance (using retrieved docs when applicable).
  6. Build prompt with policy context.
  7. Call LLM with policy temperature.
  8. Apply policy enforcement checks.
  9. Finalize request trace with status and correlation fields.

Audit Emission (Normative)
- Implementations MUST generate a per-request `request_id` for both `run` and `stream`.
- Implementations MUST derive a request-scoped `trace_id` from the active request span for both `run` and `stream`.
- Implementations MUST emit audit events during normal execution:
  - `request.received`
  - `org.resolved`
  - `retrieval.completed` (subject to logging policy level)
  - `policy.resolved` (subject to logging policy level)
  - `enforcement.passed` (run) / `enforcement.attached` (stream; subject to logging policy level)
  - `request.completed`
- Deny events MUST be emitted where exceptions are produced:
  - Governance deny (`GovernancePolicyDeniedError`) in `GovernanceRegistry`.
  - Enforcement deny (`EnforcementPolicyViolationError`) in `PolicyRegistry`.
- `request_id` MUST be propagated from engine into governance/policy registry calls so deny events are correlated.
- Audit level gating MUST follow `Policy.logging.level` semantics:
  - `minimal` emits only core lifecycle/deny/fail events.
  - `full` emits all audit events.

Failure Semantics
- Governance failures (for example missing/invalid org) MUST raise governance exceptions.
- Policy deny decisions MUST raise governance deny exceptions.
- Enforcement failures MUST raise `EnforcementPolicyViolationError`.
- Initialization failures MUST raise init/config/embedding exceptions defined in this contract.
- On failure, implementations MUST NOT return `RunResponse`/`StreamResponse`.
- Audit emission MUST NOT alter failure semantics.

Streaming Enforcement Semantics
- Implementations MAY stream chunks before final enforcement decision.
- If streaming violations are detected after full content is assembled, implementations MUST raise
  `EnforcementPolicyViolationError` at stream consumption time.

Reference Models
- `RunResponse`
  - `policy_name: str`
  - `org_id: str`
  - `user_id: str`
  - `trace_id: str | None`
  - `filter_name: str | None`
  - `retrieval_top_k: int`
  - `retrieved_count: int`
  - `enforcement_passed: bool`
  - `response: LLMResponse`
- `StreamResponse`
  - `policy_name: str`
  - `org_id: str`
  - `user_id: str`
  - `trace_id: str | None`
  - `filter_name: str | None`
  - `retrieval_top_k: int`
  - `retrieved_count: int`
  - `enforcement_passed: bool`
  - `response: LLMStreamResponse`

Reference Files
- `rag_control/core/engine.py`
- `rag_control/models/run.py`
- `rag_control/models/llm.py`
- `rag_control/spec/audit_log_contract.md`
