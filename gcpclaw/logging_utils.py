"""Logging helpers for consistent structured logs."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        if hasattr(record, "audit"):
            payload["audit"] = record.audit
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())


def emit_audit_event(
    logger: logging.Logger,
    action: str,
    actor: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> None:
    payload = {
        "schema": "gcpclaw.audit.v1",
        "timestamp": datetime.now(UTC).isoformat(),
        "action": action,
        "actor": actor,
        "status": status,
        "details": details or {},
    }
    logger.info("audit_event", extra={"event": "audit_event", "audit": payload})
