"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from opentelemetry.sdk.metrics import MeterProvider as SDKMeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from rag_control.observability import metrics as metrics_module


def test_noop_metrics_recorder_record_is_safe() -> None:
    recorder = metrics_module.NoOpMetricsRecorder()

    recorder.record("test.counter", 1.0, kind="counter")
    recorder.record("test.histogram", 100.0, kind="histogram", unit="ms", label="value")


def test_structlog_metrics_recorder_routes_kind(monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []

    def mock_logger_info(event: str, **fields: Any) -> None:
        calls.append({"event": event, **fields})

    class _MockLogger:
        def info(self, event: str, **fields: Any) -> None:
            mock_logger_info(event, **fields)

    monkeypatch.setattr(metrics_module, "configure_structlog_json", lambda: None)
    monkeypatch.setattr(structlog, "get_logger", lambda name: _MockLogger())

    recorder = metrics_module.StructlogMetricsRecorder(logger_name="test.metrics")

    recorder.record("test.counter", 42.0, kind="counter", org_id="org-1")
    recorder.record(
        "test.histogram",
        100.5,
        kind="histogram",
        unit="ms",
        org_id="org-2",
        mode="run",
    )

    assert len(calls) == 2

    assert calls[0]["event"] == "test.counter"
    assert calls[0]["category"] == "metrics"
    assert calls[0]["metric_name"] == "test.counter"
    assert calls[0]["value"] == 42.0
    assert calls[0]["kind"] == "counter"
    assert calls[0]["org_id"] == "org-1"

    assert calls[1]["event"] == "test.histogram"
    assert calls[1]["category"] == "metrics"
    assert calls[1]["metric_name"] == "test.histogram"
    assert calls[1]["value"] == 100.5
    assert calls[1]["kind"] == "histogram"
    assert calls[1]["unit"] == "ms"
    assert calls[1]["org_id"] == "org-2"
    assert calls[1]["mode"] == "run"


def test_structlog_metrics_recorder_tolerates_logger_exceptions(monkeypatch: Any) -> None:
    class _BrokenLogger:
        def info(self, event: str, **fields: Any) -> None:
            raise RuntimeError("logger failure")

    monkeypatch.setattr(metrics_module, "configure_structlog_json", lambda: None)
    monkeypatch.setattr(structlog, "get_logger", lambda name: _BrokenLogger())

    recorder = metrics_module.StructlogMetricsRecorder()
    # Should not raise
    recorder.record("test.counter", 1.0, kind="counter")


def test_otel_metrics_recorder_record_counter() -> None:
    reader = InMemoryMetricReader()
    provider = SDKMeterProvider(metric_readers=[reader])

    recorder = metrics_module.OpenTelemetryMetricsRecorder()
    # Override the meter to use our test meter provider
    recorder._meter = provider.get_meter("test")

    recorder.record(
        "test.counter",
        5.0,
        kind="counter",
        org_id="org-1",
        mode="run",
    )
    recorder.record(
        "test.counter",
        3.0,
        kind="counter",
        org_id="org-1",
        mode="run",
    )

    metrics = reader.get_metrics_data()
    assert metrics is not None
    assert len(metrics.resource_metrics) == 1
    assert len(metrics.resource_metrics[0].scope_metrics) == 1
    assert len(metrics.resource_metrics[0].scope_metrics[0].metrics) > 0


def test_otel_metrics_recorder_record_histogram() -> None:
    reader = InMemoryMetricReader()
    provider = SDKMeterProvider(metric_readers=[reader])

    recorder = metrics_module.OpenTelemetryMetricsRecorder()
    recorder._meter = provider.get_meter("test")

    recorder.record(
        "test.histogram",
        100.5,
        kind="histogram",
        unit="ms",
        org_id="org-1",
    )
    recorder.record(
        "test.histogram",
        200.5,
        kind="histogram",
        unit="ms",
        org_id="org-1",
    )

    metrics = reader.get_metrics_data()
    assert metrics is not None
    assert len(metrics.resource_metrics) == 1
    assert len(metrics.resource_metrics[0].scope_metrics) == 1
    assert len(metrics.resource_metrics[0].scope_metrics[0].metrics) > 0


def test_otel_metrics_recorder_tolerates_exceptions() -> None:
    class _BrokenMeter:
        def create_counter(self, name: str, unit: str = "") -> Any:
            raise RuntimeError("create_counter failure")

        def create_histogram(self, name: str, unit: str = "") -> Any:
            raise RuntimeError("create_histogram failure")

    recorder = metrics_module.OpenTelemetryMetricsRecorder()
    recorder._meter = cast(Any, _BrokenMeter())

    # Should not raise
    recorder.record("test.counter", 1.0, kind="counter")
    recorder.record("test.histogram", 1.0, kind="histogram")


def test_otel_metrics_recorder_reuses_instruments() -> None:
    reader = InMemoryMetricReader()
    provider = SDKMeterProvider(metric_readers=[reader])

    recorder = metrics_module.OpenTelemetryMetricsRecorder()
    recorder._meter = provider.get_meter("test")

    # Record to same counter twice
    recorder.record("test.counter", 5.0, kind="counter", org_id="org-1")
    recorder.record("test.counter", 3.0, kind="counter", org_id="org-1")

    # Check that the same instrument was reused
    assert len(recorder._counters) == 1
    assert "test.counter" in recorder._counters

    # Record to same histogram twice
    recorder.record("test.histogram", 100.0, kind="histogram", org_id="org-1")
    recorder.record("test.histogram", 200.0, kind="histogram", org_id="org-1")

    assert len(recorder._histograms) == 1
    assert "test.histogram" in recorder._histograms


def test_otel_metrics_recorder_accepts_instrumentation_version() -> None:
    # Test that the recorder can be initialized with an instrumentation_version
    recorder = metrics_module.OpenTelemetryMetricsRecorder(
        instrumentation_name="test.metrics",
        instrumentation_version="1.0.0",
    )
    assert recorder._meter is not None


def test_error_categorization_branches() -> None:
    # Test all error categorization branches for full coverage
    from rag_control.core.engine import _categorize_error, _is_denied_request

    # Test all categorization branches
    assert _categorize_error("GovernanceError") == "governance"
    assert _categorize_error("EnforcementError") == "enforcement"
    assert _categorize_error("EmbeddingError") == "embedding"
    assert _categorize_error("VectorStoreError") == "retrieval"
    assert _categorize_error("RetrievalError") == "retrieval"
    assert _categorize_error("LLMError") == "llm"
    assert _categorize_error("PolicyError") == "policy"
    assert _categorize_error("RuntimeError") == "other"

    # Test denied request categorization
    assert _is_denied_request("GovernanceError") is True
    assert _is_denied_request("EnforcementError") is True
    assert _is_denied_request("PolicyError") is True
    assert _is_denied_request("RuntimeError") is False
    assert _is_denied_request("LLMError") is False


def test_get_default_metrics_recorder_returns_otel_when_configured(monkeypatch: Any) -> None:
    monkeypatch.setattr(metrics_module, "_is_otel_metrics_configured", lambda: True)

    recorder = metrics_module.get_default_metrics_recorder()
    assert isinstance(recorder, metrics_module.OpenTelemetryMetricsRecorder)


def test_get_default_metrics_recorder_returns_structlog_when_not_configured(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(metrics_module, "_is_otel_metrics_configured", lambda: False)

    recorder = metrics_module.get_default_metrics_recorder()
    assert isinstance(recorder, metrics_module.StructlogMetricsRecorder)


def test_get_default_metrics_recorder_falls_back_on_otel_init_error(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(metrics_module, "_is_otel_metrics_configured", lambda: True)

    class _BrokenOtelRecorder:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("otel init failed")

    monkeypatch.setattr(metrics_module, "OpenTelemetryMetricsRecorder", _BrokenOtelRecorder)

    recorder = metrics_module.get_default_metrics_recorder()
    assert isinstance(recorder, metrics_module.StructlogMetricsRecorder)


def test_is_otel_metrics_configured_checks_meter_provider() -> None:
    # Test the actual _is_otel_metrics_configured function
    result = metrics_module._is_otel_metrics_configured()
    # Result depends on whether OTel SDK MeterProvider is configured
    # We just verify it returns a boolean without error
    assert isinstance(result, bool)


def test_policy_registry_violation_categorization() -> None:
    from rag_control.policy.policy import PolicyRegistry

    categorize = PolicyRegistry._categorize_violation

    # Test max_output_tokens violation
    assert (
        categorize("completion tokens exceed enforcement.max_output_tokens (750 > 500)")
        == "max_output_tokens"
    )
    # Test missing_citations violation
    assert (
        categorize("missing citations while generation.require_citations=true")
        == "missing_citations"
    )
    # Test invalid_citations violation
    assert categorize("invalid citations out of retrieved range: [5, 6]") == "invalid_citations"
    # Test external_knowledge violation
    ext_knowledge_msg = (
        "response may rely on external knowledge: citations are required "
        "when enforcement.prevent_external_knowledge=true"
    )
    assert categorize(ext_knowledge_msg) == "external_knowledge"
    # Test strict_fallback violation
    assert (
        categorize("response must use strict fallback when no documents are retrieved")
        == "strict_fallback"
    )
    # Test unknown violation
    assert categorize("unknown violation type") == "unknown"
