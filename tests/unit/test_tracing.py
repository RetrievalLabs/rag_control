"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from opentelemetry.trace import SpanKind

from rag_control.observability import tracing as tracing_module


def test_noop_tracer_start_span_event_finish_is_safe() -> None:
    tracer = tracing_module.NoOpTracer()
    span = tracer.start_span("noop")

    assert isinstance(span.trace_id, str)
    assert isinstance(span.span_id, str)
    assert span.trace_id
    assert span.span_id

    span.event("transition.test", key="value")
    span.finish(status="ok")
    span.finish(status="error", error_type="X", error_message="Y")


def test_to_otel_span_kind_maps_known_values_and_defaults_to_internal() -> None:
    for kind, expected in (
        ("internal", SpanKind.INTERNAL),
        ("server", SpanKind.SERVER),
        ("client", SpanKind.CLIENT),
        ("producer", SpanKind.PRODUCER),
        ("consumer", SpanKind.CONSUMER),
    ):
        assert tracing_module._to_otel_span_kind(kind) is expected

    assert tracing_module._to_otel_span_kind("unknown-kind") is SpanKind.INTERNAL


def test_to_otel_attributes_converts_values_and_adds_semconv_aliases() -> None:
    attrs = tracing_module._to_otel_attributes(
        {
            "none_val": None,
            "scalar": "ok",
            "bool_val": True,
            "int_val": 1,
            "float_val": 1.5,
            "plain_list": [1, "a"],
            "mixed_list": [1, {"x": 1}],
            "obj": object(),
            "user_id": "u-1",
            "llm_model": "gpt-test",
            "prompt_tokens": 10,
            "exception.type": "AlreadySet",
            "error_type": "IgnoredByAliasBecauseExists",
        }
    )

    assert "none_val" not in attrs
    assert attrs["scalar"] == "ok"
    assert attrs["bool_val"] is True
    assert attrs["int_val"] == 1
    assert attrs["float_val"] == 1.5
    assert attrs["plain_list"] == [1, "a"]
    assert isinstance(attrs["mixed_list"], str)
    assert isinstance(attrs["obj"], str)

    assert attrs["enduser.id"] == "u-1"
    assert attrs["gen_ai.request.model"] == "gpt-test"
    assert attrs["gen_ai.usage.input_tokens"] == 10
    assert attrs["exception.type"] == "AlreadySet"


def test_get_default_tracer_selection_branches(monkeypatch: Any) -> None:
    class _SentinelOtelTracer:
        pass

    monkeypatch.setattr(tracing_module, "_is_otel_configured", lambda: False)
    tracer = tracing_module.get_default_tracer()
    assert isinstance(tracer, tracing_module.StructlogTracer)

    monkeypatch.setattr(tracing_module, "_is_otel_configured", lambda: True)
    monkeypatch.setattr(tracing_module, "OpenTelemetryTracer", _SentinelOtelTracer)
    tracer = tracing_module.get_default_tracer()
    assert isinstance(tracer, _SentinelOtelTracer)

    class _BrokenOtelTracer:
        def __init__(self) -> None:
            raise RuntimeError("otel init failed")

    monkeypatch.setattr(tracing_module, "OpenTelemetryTracer", _BrokenOtelTracer)
    tracer = tracing_module.get_default_tracer()
    assert isinstance(tracer, tracing_module.StructlogTracer)


def test_structlog_tracer_uses_active_span_for_parent_linkage() -> None:
    tracer = tracing_module.StructlogTracer(logger_name="tests.trace")

    parent = tracer.start_span("parent")
    child = tracer.start_span("child")
    assert child.trace_id == parent.trace_id
    assert getattr(child, "_parent_span_id") == parent.span_id
    child.finish()
    parent.finish()


def test_open_telemetry_trace_span_tolerates_internal_exceptions() -> None:
    @dataclass
    class _SpanContext:
        trace_id: int = 1
        span_id: int = 2

    class _BrokenSpan:
        def get_span_context(self) -> _SpanContext:
            return _SpanContext()

        def add_event(self, name: str, attributes: dict[str, Any]) -> None:
            raise RuntimeError("add_event failure")

        def set_attributes(self, attributes: dict[str, Any]) -> None:
            raise RuntimeError("set_attributes failure")

        def set_attribute(self, key: str, value: Any) -> None:
            raise RuntimeError("set_attribute failure")

        def set_status(self, status: Any) -> None:
            raise RuntimeError("set_status failure")

        def end(self) -> None:
            raise RuntimeError("end failure")

    wrapped = tracing_module._OpenTelemetryTraceSpan(_BrokenSpan(), detach_token=object())
    wrapped.event("test.event", x=1)
    wrapped.finish(status="error", error_type="Err", error_message="boom", key="value")
    wrapped.finish(status="ok")


def test_structlog_trace_span_tolerates_logger_emit_and_context_reset_failures() -> None:
    class _BrokenLogger:
        def info(self, event: str, **fields: Any) -> None:
            raise RuntimeError("logger failure")

    span = tracing_module._StructlogTraceSpan(cast(Any, _BrokenLogger()), name="broken")
    span.event("step")

    # Force reset failure branch; tracing must still remain safe.
    span._context_token = object()  # type: ignore[assignment]
    span.finish(status="ok")


def test_open_telemetry_trace_span_event_returns_early_after_finish() -> None:
    @dataclass
    class _SpanContext:
        trace_id: int = 11
        span_id: int = 22

    class _Span:
        def __init__(self) -> None:
            self.event_calls = 0
            self.ended = False

        def get_span_context(self) -> _SpanContext:
            return _SpanContext()

        def add_event(self, name: str, attributes: dict[str, Any]) -> None:
            self.event_calls += 1

        def set_attributes(self, attributes: dict[str, Any]) -> None:
            return None

        def set_attribute(self, key: str, value: Any) -> None:
            return None

        def set_status(self, status: Any) -> None:
            return None

        def end(self) -> None:
            self.ended = True

    raw_span = _Span()
    wrapped = tracing_module._OpenTelemetryTraceSpan(raw_span, detach_token=object())
    wrapped.finish(status="ok")
    wrapped.event("after.finish")

    assert raw_span.ended is True
    assert raw_span.event_calls == 0
