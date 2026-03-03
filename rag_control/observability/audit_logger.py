"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Any, Literal, Protocol

import structlog

AuditLogLevel = Literal["debug", "info", "warning", "error", "critical"]
AuditLogPolicyLevel = Literal["minimal", "full"]

_STRUCTLOG_CONFIGURED = False


class AuditLogger(Protocol):
    def log_event(self, event: str, *, level: AuditLogLevel = "info", **fields: Any) -> None: ...


class NoOpAuditLogger:
    def log_event(self, event: str, *, level: AuditLogLevel = "info", **fields: Any) -> None:
        return None


class StructlogAuditLogger:
    def __init__(self, logger_name: str = "rag_control.audit") -> None:
        configure_structlog_json()
        self._logger = structlog.get_logger(logger_name)

    def log_event(self, event: str, *, level: AuditLogLevel = "info", **fields: Any) -> None:
        payload = {"category": "audit", **fields}
        if level == "debug":
            self._logger.debug(event, **payload)
            return
        if level == "warning":
            self._logger.warning(event, **payload)
            return
        if level == "error":
            self._logger.error(event, **payload)
            return
        if level == "critical":
            self._logger.critical(event, **payload)
            return
        self._logger.info(event, **payload)


def should_emit_audit_event(
    event: str,
    logging_level: AuditLogPolicyLevel | None,
) -> bool:
    if logging_level is None or logging_level == "full":
        return True
    if logging_level == "minimal":
        return event in {
            "request.received",
            "org.resolved",
            "request.completed",
            "request.denied",
            "request.failed",
        }
    return True


@dataclass(slots=True)
class AuditLoggingContext:
    logger: AuditLogger
    mode: Literal["run", "stream"]
    request_id: str
    org_id: str | None
    user_id: str | None
    logging_level: AuditLogPolicyLevel | None = None
    component: str = "rag_control.engine"
    sdk_name: str = "rag_control"
    sdk_version: str = "unknown"
    company_name: str = "RetrievalLabs"

    def log_event(self, event: str, *, level: AuditLogLevel = "info", **fields: Any) -> None:
        if not should_emit_audit_event(event, self.logging_level):
            return
        self.logger.log_event(
            event,
            level=level,
            component=self.component,
            sdk_name=self.sdk_name,
            sdk_version=self.sdk_version,
            company_name=self.company_name,
            mode=self.mode,
            request_id=self.request_id,
            org_id=self.org_id,
            user_id=self.user_id,
            **fields,
        )


def configure_structlog_json() -> None:
    global _STRUCTLOG_CONFIGURED
    if _STRUCTLOG_CONFIGURED:
        return

    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    _STRUCTLOG_CONFIGURED = True
