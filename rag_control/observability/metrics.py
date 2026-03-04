"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol

import structlog
from opentelemetry import metrics as otel_metrics
from opentelemetry.sdk.metrics import MeterProvider as SDKMeterProvider

from .audit_logger import configure_structlog_json

MetricKind = Literal["counter", "histogram"]


class MetricsRecorder(Protocol):
    def record(
        self,
        name: str,
        value: float,
        *,
        kind: MetricKind = "counter",
        unit: str = "",
        **labels: str,
    ) -> None: ...


class NoOpMetricsRecorder:
    def record(
        self,
        name: str,
        value: float,
        *,
        kind: MetricKind = "counter",
        unit: str = "",
        **labels: str,
    ) -> None:
        return None


class StructlogMetricsRecorder:
    def __init__(self, logger_name: str = "rag_control.metrics") -> None:
        configure_structlog_json()
        self._logger = structlog.get_logger(logger_name)

    def record(
        self,
        name: str,
        value: float,
        *,
        kind: MetricKind = "counter",
        unit: str = "",
        **labels: str,
    ) -> None:
        try:
            self._logger.info(
                name,
                category="metrics",
                metric_name=name,
                value=value,
                kind=kind,
                unit=unit,
                **labels,
            )
        except Exception:
            # Metrics must not affect engine behavior.
            return


class OpenTelemetryMetricsRecorder:
    def __init__(
        self,
        instrumentation_name: str = "rag_control",
        instrumentation_version: str | None = None,
    ) -> None:
        if instrumentation_version is not None:
            self._meter = otel_metrics.get_meter(
                instrumentation_name,
                instrumentation_version,
            )
        else:
            self._meter = otel_metrics.get_meter(instrumentation_name)
        self._counters: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}

    def record(
        self,
        name: str,
        value: float,
        *,
        kind: MetricKind = "counter",
        unit: str = "",
        **labels: str,
    ) -> None:
        try:
            if kind == "counter":
                counter = self._counters.setdefault(
                    name,
                    self._meter.create_counter(name, unit=unit),
                )
                counter.add(value, attributes=labels if labels else None)
            elif kind == "histogram":
                histogram = self._histograms.setdefault(
                    name,
                    self._meter.create_histogram(name, unit=unit),
                )
                histogram.record(value, attributes=labels if labels else None)
        except Exception:
            # Metrics must not affect engine behavior.
            return


def _is_otel_metrics_configured() -> bool:
    return isinstance(otel_metrics.get_meter_provider(), SDKMeterProvider)


def get_default_metrics_recorder() -> MetricsRecorder:
    if _is_otel_metrics_configured():
        try:
            return OpenTelemetryMetricsRecorder()
        except Exception:
            return StructlogMetricsRecorder()
    return StructlogMetricsRecorder()
