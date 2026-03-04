Tracing Contract

Version: v2026.1
Status: Draft
Applies To:
- `rag_control.core.engine.RAGControl`
- `rag_control.observability.tracing.Tracer`
- `rag_control.observability.tracing.TraceSpan`

Purpose
- Define request tracing behavior for governed RAG execution.
- Define correlation requirements between tracing and audit outputs.

Normative Terms
- MUST: required.
- SHOULD: recommended unless system constraints prevent it.
- MAY: optional.

Tracing Interface
- Tracer implementations MUST provide:
  - `start_span(name: str, **fields: Any) -> TraceSpan`
- Returned span implementations MUST provide:
  - `trace_id: str`
  - `span_id: str`
  - `event(event: str, **fields: Any) -> None`
  - `finish(status: "ok" | "error" = "ok", error_type: str | None = None, error_message: str | None = None, **fields: Any) -> None`

Engine Tracing Behavior
- `RAGControl.run` and `RAGControl.stream` MUST each create exactly one request span.
- Span naming taxonomy MUST follow:
  - Root span: `rag_control.request.<mode>` where `<mode>` is `run` or `stream`.
  - Stage span: `rag_control.request.<mode>.stage.<stage_name>`.
  - Stage names SHOULD be stable dotted identifiers (for example `policy.resolve`, `llm.generate`).
- Trace correlation MUST use `TraceSpan.trace_id` from the started span and pass it to the audit context and response model.
- OpenTelemetry-backed tracing MUST follow active context semantics:
  - if an active parent span exists, the request span MUST be created as a child span.
  - if no active parent span exists, the request span MUST be created as a root span.
- Span events SHOULD cover key execution stages:
  - request receipt
  - org lookup
  - embedding
  - retrieval
  - policy resolution
  - prompt build
  - LLM invocation
  - enforcement
- Root span MUST be finished with:
  - `status="ok"` on success
  - `status="error"` and error metadata on exception

Response Correlation
- `RunResponse.trace_id` and `StreamResponse.trace_id` MUST contain the request trace ID.
- Audit events SHOULD include `trace_id` so audit and trace streams can be joined.

Failure Semantics
- Tracing failures MUST NOT alter core execution outcomes.
- Business exceptions MUST retain their original types and messages.

Reference Files
- `rag_control/core/engine.py`
- `rag_control/observability/tracing.py`
- `rag_control/models/run.py`
