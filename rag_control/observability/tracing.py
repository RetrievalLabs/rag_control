"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

import time
from contextvars import ContextVar
from typing import Any, Literal, Protocol
from uuid import uuid4

from opentelemetry import context as otel_context
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
from opentelemetry.trace import Status, StatusCode
import structlog

from .audit_logger import configure_structlog_json

TraceStatus = Literal["ok", "error"]
_STRUCTLOG_ACTIVE_SPAN: ContextVar[tuple[str, str] | None] = ContextVar(
    "rag_control_structlog_active_span",
    default=None,
)


class TraceSpan(Protocol):
    span_id: str
    trace_id: str

    def event(self, event: str, **fields: Any) -> None: ...

    def finish(
        self,
        *,
        status: TraceStatus = "ok",
        error_type: str | None = None,
        error_message: str | None = None,
        **fields: Any,
    ) -> None: ...


class Tracer(Protocol):
    def start_span(self, name: str, **fields: Any) -> TraceSpan: ...


class NoOpTraceSpan:
    def __init__(self) -> None:
        self.trace_id = str(uuid4())
        self.span_id = str(uuid4())

    def event(self, event: str, **fields: Any) -> None:
        return None

    def finish(
        self,
        *,
        status: TraceStatus = "ok",
        error_type: str | None = None,
        error_message: str | None = None,
        **fields: Any,
    ) -> None:
        return None


class NoOpTracer:
    def start_span(self, name: str, **fields: Any) -> TraceSpan:
        return NoOpTraceSpan()


class _StructlogTraceSpan:
    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        *,
        name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        span_id: str | None = None,
        **fields: Any,
    ) -> None:
        self._logger = logger
        self._name = name
        self.trace_id = trace_id if trace_id is not None else str(uuid4())
        self._parent_span_id = parent_span_id
        self.span_id = span_id if span_id is not None else str(uuid4())
        self._start_time = time.perf_counter()
        self._finished = False
        self._context_token: object | None = None
        self._emit("span.started", span_name=name, **fields)

    def event(self, event: str, **fields: Any) -> None:
        self._emit("span.event", span_name=self._name, event_name=event, **fields)

    def finish(
        self,
        *,
        status: TraceStatus = "ok",
        error_type: str | None = None,
        error_message: str | None = None,
        **fields: Any,
    ) -> None:
        if self._finished:
            return
        self._finished = True
        duration_ms = (time.perf_counter() - self._start_time) * 1000
        self._emit(
            "span.finished",
            span_name=self._name,
            status=status,
            duration_ms=duration_ms,
            error_type=error_type,
            error_message=error_message,
            **fields,
        )
        if self._context_token is not None:
            try:
                _STRUCTLOG_ACTIVE_SPAN.reset(self._context_token)
            except Exception:
                return

    def _emit(self, event: str, **fields: Any) -> None:
        try:
            self._logger.info(
                event,
                category="trace",
                trace_id=self.trace_id,
                span_id=self.span_id,
                parent_span_id=self._parent_span_id,
                **fields,
            )
        except Exception:
            # Tracing must not affect engine behavior.
            return


class StructlogTracer:
    def __init__(self, logger_name: str = "rag_control.trace") -> None:
        configure_structlog_json()
        self._logger = structlog.get_logger(logger_name)

    def start_span(self, name: str, **fields: Any) -> TraceSpan:
        trace_id = fields.pop("trace_id", None)
        parent_span_id = fields.pop("parent_span_id", None)
        if trace_id is None and parent_span_id is None:
            active_span = _STRUCTLOG_ACTIVE_SPAN.get()
            if active_span is not None:
                trace_id, parent_span_id = active_span

        span = _StructlogTraceSpan(
            self._logger,
            name=name,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            **fields,
        )
        span._context_token = _STRUCTLOG_ACTIVE_SPAN.set((span.trace_id, span.span_id))
        return span


class _OpenTelemetryTraceSpan:
    def __init__(
        self,
        span: Any,
        *,
        detach_token: object,
    ) -> None:
        self._span = span
        self._detach_token = detach_token
        self._finished = False

        span_context = span.get_span_context()
        self.trace_id = f"{span_context.trace_id:032x}"
        self.span_id = f"{span_context.span_id:016x}"

    def event(self, event: str, **fields: Any) -> None:
        if self._finished:
            return
        try:
            self._span.add_event(event, attributes=_to_otel_attributes(fields))
        except Exception:
            return

    def finish(
        self,
        *,
        status: TraceStatus = "ok",
        error_type: str | None = None,
        error_message: str | None = None,
        **fields: Any,
    ) -> None:
        if self._finished:
            return
        self._finished = True
        try:
            if fields:
                self._span.set_attributes(_to_otel_attributes(fields))
            if status == "error":
                if error_type is not None:
                    self._span.set_attribute("error.type", error_type)
                if error_message is not None:
                    self._span.set_attribute("error.message", error_message)
                self._span.set_status(Status(StatusCode.ERROR, description=error_message))
            else:
                self._span.set_status(Status(StatusCode.OK))
            self._span.end()
        except Exception:
            return
        finally:
            try:
                otel_context.detach(self._detach_token)
            except Exception:
                pass


class OpenTelemetryTracer:
    def __init__(
        self,
        instrumentation_name: str = "rag_control",
        instrumentation_version: str | None = None,
    ) -> None:
        self._tracer = otel_trace.get_tracer(
            instrumentation_name,
            instrumentation_version,
        )

    def start_span(self, name: str, **fields: Any) -> TraceSpan:
        fields.pop("trace_id", None)
        fields.pop("parent_span_id", None)
        span = self._tracer.start_span(name)
        detach_token = otel_context.attach(otel_trace.set_span_in_context(span))
        span.set_attributes(_to_otel_attributes(fields))
        return _OpenTelemetryTraceSpan(span, detach_token=detach_token)


def _is_otel_configured() -> bool:
    return isinstance(otel_trace.get_tracer_provider(), SDKTracerProvider)


def _to_otel_attributes(fields: dict[str, Any]) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (bool, int, float, str)):
            attributes[key] = value
            continue
        if isinstance(value, (list, tuple)):
            if all(isinstance(item, (bool, int, float, str)) for item in value):
                attributes[key] = list(value)
                continue
            attributes[key] = str(value)
            continue
        attributes[key] = str(value)
    return attributes


def get_default_tracer() -> Tracer:
    if _is_otel_configured():
        try:
            return OpenTelemetryTracer()
        except Exception:
            return StructlogTracer()
    return StructlogTracer()
