Metrics Contract

Version: v2026.1
Status: Draft
Applies To:
- `rag_control.core.engine.RAGControl`
- `rag_control.observability.metrics.MetricsRecorder`

Purpose
- Define request metrics recording behavior for governed RAG execution.
- Define metric schemas and label cardinality for monitoring and alerting.

Normative Terms
- MUST: required.
- SHOULD: recommended unless system constraints prevent it.
- MAY: optional.

Metrics Interface
- MetricsRecorder implementations MUST provide:
  - `record(name: str, value: float, *, kind: MetricKind = "counter", unit: str = "", **labels: str) -> None`
- Kind values MUST be one of:
  - `"counter"`: monotonically increasing, suitable for counts and accumulated values
  - `"histogram"`: distribution of values, suitable for durations and sizes

Engine Metrics Behavior
- `RAGControl.run` and `RAGControl.stream` MUST each record:
  - `rag_control.requests` counter with labels: `mode`, `org_id`, `status`
  - `rag_control.request.duration_ms` histogram with labels: `mode`, `org_id`, `status`
- Per-stage metrics recording:
  - Each stage execution MUST record `rag_control.stage.duration_ms` histogram with labels: `mode`, `org_id`, `stage`, `status`
- Retrieval metrics:
  - `rag_control.retrieval.document_count` histogram recording count of retrieved documents with labels: `mode`, `org_id`
- LLM metrics (when `response.usage` is not None):
  - `rag_control.llm.prompt_tokens` counter with labels: `mode`, `org_id`, `model`
  - `rag_control.llm.completion_tokens` counter with labels: `mode`, `org_id`, `model`

Metric Schema Reference

| Metric name | Kind | Unit | Labels | When |
|---|---|---|---|---|
| `rag_control.requests` | counter | — | `mode`, `org_id`, `status` | On request completion or error |
| `rag_control.request.duration_ms` | histogram | ms | `mode`, `org_id`, `status` | On request completion or error |
| `rag_control.stage.duration_ms` | histogram | ms | `mode`, `org_id`, `stage`, `status` | After each stage completes |
| `rag_control.retrieval.document_count` | histogram | — | `mode`, `org_id` | On successful retrieval |
| `rag_control.llm.prompt_tokens` | counter | — | `mode`, `org_id`, `model` | When LLM response includes usage |
| `rag_control.llm.completion_tokens` | counter | — | `mode`, `org_id`, `model` | When LLM response includes usage |

Label Values
- `mode`: one of `"run"` or `"stream"`
- `org_id`: organization identifier (empty string if None)
- `status`: one of `"ok"` or `"error"`
- `stage`: stable dotted identifier (e.g. `org_lookup`, `embedding`, `retrieval`, `policy.resolve`, `prompt.build`, `llm.generate`, `llm.stream`, `enforcement`)
- `model`: model name from response metadata

Failure Semantics
- Metrics recording failures MUST NOT alter core execution outcomes.
- Business exceptions MUST retain their original types and messages.
- All metrics implementations MUST swallow exceptions internally (following the noop-safe pattern).

Reference Files
- `rag_control/core/engine.py`
- `rag_control/observability/metrics.py`
