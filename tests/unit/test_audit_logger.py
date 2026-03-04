"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag_control.observability import audit_logger as audit_logger_module


@dataclass
class _CapturedEvent:
    event: str
    level: str
    fields: dict[str, Any]


class _CapturedAuditLogger:
    def __init__(self) -> None:
        self.events: list[_CapturedEvent] = []

    def log_event(self, event: str, *, level: str = "info", **fields: Any) -> None:
        self.events.append(_CapturedEvent(event=event, level=level, fields=fields))


class _CapturedStructlogLogger:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def debug(self, event: str, **payload: Any) -> None:
        self.calls.append(("debug", event, payload))

    def info(self, event: str, **payload: Any) -> None:
        self.calls.append(("info", event, payload))

    def warning(self, event: str, **payload: Any) -> None:
        self.calls.append(("warning", event, payload))

    def error(self, event: str, **payload: Any) -> None:
        self.calls.append(("error", event, payload))

    def critical(self, event: str, **payload: Any) -> None:
        self.calls.append(("critical", event, payload))


def test_noop_audit_logger_log_event_is_safe() -> None:
    logger = audit_logger_module.NoOpAuditLogger()
    logger.log_event("request.received", level="debug", request_id="req-1")


def test_should_emit_audit_event_respects_minimal_policy() -> None:
    assert audit_logger_module.should_emit_audit_event("request.received", "minimal") is True
    assert audit_logger_module.should_emit_audit_event("request.completed", "minimal") is True
    assert audit_logger_module.should_emit_audit_event("retrieval.completed", "minimal") is False
    assert audit_logger_module.should_emit_audit_event("anything", "full") is True
    assert audit_logger_module.should_emit_audit_event("anything", None) is True


def test_audit_logging_context_adds_common_fields_and_filters_events() -> None:
    captured = _CapturedAuditLogger()
    context = audit_logger_module.AuditLoggingContext(
        logger=captured,
        mode="run",
        request_id="req-ctx-1",
        org_id="org-1",
        user_id="user-1",
        trace_id="trace-1",
        logging_level="minimal",
    )

    context.log_event("retrieval.completed", level="info", retrieved_count=2)
    context.log_event("request.completed", level="info", retrieved_count=2)

    assert len(captured.events) == 1
    event = captured.events[0]
    assert event.event == "request.completed"
    assert event.level == "info"
    assert event.fields["component"] == "rag_control.engine"
    assert event.fields["sdk_name"] == "rag_control"
    assert event.fields["company_name"] == "RetrievalLabs"
    assert event.fields["mode"] == "run"
    assert event.fields["request_id"] == "req-ctx-1"
    assert event.fields["trace_id"] == "trace-1"
    assert event.fields["org_id"] == "org-1"
    assert event.fields["user_id"] == "user-1"
    assert event.fields["retrieved_count"] == 2


def test_structlog_audit_logger_routes_level_methods(monkeypatch: Any) -> None:
    captured = _CapturedStructlogLogger()
    monkeypatch.setattr(audit_logger_module, "configure_structlog_json", lambda: None)
    monkeypatch.setattr(audit_logger_module.structlog, "get_logger", lambda _: captured)

    logger = audit_logger_module.StructlogAuditLogger("tests.audit")
    logger.log_event("ev.debug", level="debug", a=1)
    logger.log_event("ev.warning", level="warning", b=2)
    logger.log_event("ev.error", level="error", c=3)
    logger.log_event("ev.critical", level="critical", d=4)
    logger.log_event("ev.info", level="info", e=5)

    assert [level for level, _, _ in captured.calls] == [
        "debug",
        "warning",
        "error",
        "critical",
        "info",
    ]
    for _, _, payload in captured.calls:
        assert payload["category"] == "audit"


def test_configure_structlog_json_is_idempotent(monkeypatch: Any) -> None:
    basic_config_calls: list[dict[str, Any]] = []
    configure_calls: list[dict[str, Any]] = []

    monkeypatch.setattr(
        audit_logger_module.logging,
        "basicConfig",
        lambda **kwargs: basic_config_calls.append(kwargs),
    )
    monkeypatch.setattr(
        audit_logger_module.structlog,
        "configure",
        lambda **kwargs: configure_calls.append(kwargs),
    )
    monkeypatch.setattr(audit_logger_module, "_STRUCTLOG_CONFIGURED", False)

    audit_logger_module.configure_structlog_json()
    audit_logger_module.configure_structlog_json()

    assert len(basic_config_calls) == 1
    assert len(configure_calls) == 1
