Metrics Contract

Version: v2026.1
Status: Draft
Applies To:
- `rag_control.core.engine.RAGControl`
- `rag_control.observability.metrics.MetricsRecorder`

Purpose
- Define request metrics recording behavior for governed RAG execution.
- Define metric schemas and label cardinality for monitoring and alerting.
- Enable operational visibility, performance monitoring, and cost tracking.

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
  - `rag_control.retrieval.document_score` histogram recording average document relevance scores
  - `rag_control.retrieval.top_document_score` histogram recording top document relevance score
- Query metrics:
  - `rag_control.query.length_chars` histogram recording query string length
- Policy metrics:
  - `rag_control.policy.resolved_by_name` counter recording which policies were selected with label: `policy_name`
- LLM metrics (when `response.usage` is not None):
  - `rag_control.llm.prompt_tokens` counter with labels: `mode`, `org_id`, `model`
  - `rag_control.llm.completion_tokens` counter with labels: `mode`, `org_id`, `model`
  - `rag_control.llm.total_tokens` counter (prompt + completion) with labels: `mode`, `org_id`, `model`
  - `rag_control.llm.token_efficiency` histogram (completion / prompt ratio) with labels: `mode`, `org_id`, `model`
- Embedding metrics:
  - `rag_control.embedding.dimensions` histogram recording embedding vector dimensions
- Error metrics (on request failure):
  - `rag_control.errors_by_type` counter with labels: `mode`, `org_id`, `error_type`
  - `rag_control.errors_by_category` counter with labels: `mode`, `org_id`, `error_category`
  - `rag_control.requests.denied` counter (for denied requests only) with labels: `mode`, `org_id`, `denial_reason`

Metric Schema Reference

| Metric name | Kind | Unit | Labels | When |
|---|---|---|---|---|
| `rag_control.requests` | counter | — | `mode`, `org_id`, `status` | On request completion or error |
| `rag_control.request.duration_ms` | histogram | ms | `mode`, `org_id`, `status` | On request completion or error |
| `rag_control.stage.duration_ms` | histogram | ms | `mode`, `org_id`, `stage`, `status` | After each stage completes |
| `rag_control.retrieval.document_count` | histogram | — | `mode`, `org_id` | On successful retrieval |
| `rag_control.retrieval.document_score` | histogram | — | `mode`, `org_id` | On successful retrieval (avg score) |
| `rag_control.retrieval.top_document_score` | histogram | — | `mode`, `org_id` | On successful retrieval (top score) |
| `rag_control.query.length_chars` | histogram | — | `mode`, `org_id` | On request completion |
| `rag_control.policy.resolved_by_name` | counter | — | `mode`, `org_id`, `policy_name` | On successful policy resolution |
| `rag_control.llm.prompt_tokens` | counter | — | `mode`, `org_id`, `model` | When LLM response includes usage |
| `rag_control.llm.completion_tokens` | counter | — | `mode`, `org_id`, `model` | When LLM response includes usage |
| `rag_control.llm.total_tokens` | counter | — | `mode`, `org_id`, `model` | When LLM response includes usage |
| `rag_control.llm.token_efficiency` | histogram | — | `mode`, `org_id`, `model` | When LLM response includes usage |
| `rag_control.embedding.dimensions` | histogram | — | `mode`, `org_id`, `model` | After embedding stage |
| `rag_control.errors_by_type` | counter | — | `mode`, `org_id`, `error_type` | On request error |
| `rag_control.errors_by_category` | counter | — | `mode`, `org_id`, `error_category` | On request error |
| `rag_control.requests.denied` | counter | — | `mode`, `org_id`, `denial_reason` | When request is denied (governance/enforcement/policy) |

Label Values
- `mode`: one of `"run"` or `"stream"`
- `org_id`: organization identifier (empty string if None)
- `status`: one of `"ok"` or `"error"`
- `stage`: stable dotted identifier (e.g. `org_lookup`, `embedding`, `retrieval`, `policy.resolve`, `prompt.build`, `llm.generate`, `llm.stream`, `enforcement`)
- `model`: model name from response metadata
- `error_type`: exception class name (e.g. `GovernanceRegistryOrgNotFoundError`, `EnforcementPolicyViolationError`)
- `error_category`: one of `governance`, `enforcement`, `embedding`, `retrieval`, `llm`, `policy`, `other`
- `denial_reason`: one of `governance`, `enforcement`, `policy` (subset of error_category for denied requests)
- `policy_name`: name of the resolved policy

Failure Semantics
- Metrics recording failures MUST NOT alter core execution outcomes.
- Business exceptions MUST retain their original types and messages.
- All metrics implementations MUST swallow exceptions internally (following the noop-safe pattern).

Reference Files
- `rag_control/core/engine.py`
- `rag_control/observability/metrics.py`
