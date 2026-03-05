Audit Log Contract

Version: v2026.1
Status: Draft
Applies To:
- `rag_control.core.engine.RAGControl`
- `rag_control.governance.gov.GovernanceRegistry`
- `rag_control.policy.policy.PolicyRegistry`
- `rag_control.observability.audit_logger.AuditLogger`
- `rag_control.observability.audit_logger.should_emit_audit_event`

Purpose
- Define the audit-event contract emitted by governed RAG execution.
- Define required event fields for correlation and compliance.
- Define policy-level behavior differences for `minimal` and `full`.

Normative Terms
- MUST: required.
- SHOULD: recommended unless system constraints prevent it.
- MAY: optional.

Audit Logger Interface
- Audit logger implementations MUST provide:
  - `log_event(event: str, *, level: AuditLogLevel = "info", **fields: Any) -> None`
- Default implementation (`StructlogAuditLogger`) MUST emit JSON-structured events.

Global Audit Fields
- Every emitted audit event MUST include:
  - `event: str`
  - `level: "debug" | "info" | "warning" | "error" | "critical"`
  - `component: "rag_control.engine"`
  - `sdk_name: "rag_control"`
  - `sdk_version: str`
  - `company_name: "RetrievalLabs"`
- Request-scoped events SHOULD include:
  - `request_id: str`
  - `trace_id: str | None`
  - `org_id: str | None`
  - `user_id: str | None`

Core Event Set
- Implementations SHOULD use these event names:
  - `request.received`
  - `org.resolved`
  - `retrieval.completed`
  - `policy.resolved`
  - `enforcement.passed`
  - `enforcement.attached` (stream flow)
  - `request.completed`
  - `request.denied`
  - `request.failed`

Audit Emission Points
- `RAGControl` MUST emit:
  - `request.received` at request start.
  - `org.resolved` after org lookup succeeds.
  - `retrieval.completed` after retrieval succeeds.
    - Event SHOULD include:
      - `retrieved_count: int`
      - `retrieved_doc_ids: list[str]`
  - `policy.resolved` after policy resolution succeeds.
  - `enforcement.passed` for successful non-stream enforcement.
  - `enforcement.attached` when stream enforcement wrapper is attached.
  - `request.completed` after successful execution response assembly.
    - Event SHOULD include `retrieved_doc_ids: list[str]`.
    - Event SHOULD include LLM execution details:
      - `llm_model: str | None`
      - `llm_temperature: float`
      - `prompt_tokens: int | None`
      - `completion_tokens: int | None`
      - `total_tokens: int | None`
- `GovernanceRegistry` MUST emit `request.denied` when a deny rule matches, before raising `GovernancePolicyDeniedError`.
  - Event SHOULD include `rule_name`.
- `PolicyRegistry` MUST emit `request.denied` when enforcement violations are detected, before raising `EnforcementPolicyViolationError`.
  - Event SHOULD include `violations: list[str]`.

Request Correlation
- `request_id` MUST be generated once per `run`/`stream` request.
- `request_id` MUST be propagated to:
  - governance policy resolution (`GovernanceRegistry.resolve_policy`)
  - policy enforcement (`PolicyRegistry.enforce_response`)
  - stream policy enforcement wrapper (`PolicyRegistry.enforce_stream_response`)
- Deny events emitted from governance/policy registries MUST include the same `request_id`.

Logging Policy Levels
- Source policy:
  - `Policy.logging.level` (`minimal | full`)
- `minimal`:
  - MUST emit only:
    - `request.received`
    - `org.resolved`
    - `request.completed`
    - `request.denied`
    - `error.occurred`
  - MUST suppress:
    - `retrieval.completed`
    - `policy.resolved`
    - `enforcement.passed`
    - `enforcement.attached`
- `full`:
  - MUST emit all audit events.

Failure Semantics
- Audit emission MUST NOT change business outcomes:
  - If audit logging fails internally, core exception and execution semantics SHOULD remain unchanged.
- Governance deny path MUST raise `GovernancePolicyDeniedError`.
- Enforcement deny path MUST raise `EnforcementPolicyViolationError`.

Security and Data Handling
- Audit events SHOULD avoid raw sensitive payloads unless explicitly required by policy.
- Implementations SHOULD prefer identifiers and metadata over full content bodies.

Reference Files
- `rag_control/core/engine.py`
- `rag_control/governance/gov.py`
- `rag_control/policy/policy.py`
- `rag_control/observability/audit_logger.py`
