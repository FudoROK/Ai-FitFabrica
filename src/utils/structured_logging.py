"""Centralized structured logging configuration for Cloud Logging compatibility."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

_RESERVED_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys())
_MANAGED_STRUCTURED_HANDLER_FLAG = "_soulfabrica_managed_structured_handler"


class CloudJsonFormatter(logging.Formatter):
    """Serialize log records into one-line JSON objects for Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "message": record.getMessage(),
            "severity": record.levelname,
            "logger": record.name,
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_FIELDS:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))


def _is_managed_structured_handler(handler: logging.Handler) -> bool:
    return bool(getattr(handler, _MANAGED_STRUCTURED_HANDLER_FLAG, False))


def _build_managed_structured_handler(level: int) -> logging.Handler:
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(CloudJsonFormatter())
    setattr(handler, _MANAGED_STRUCTURED_HANDLER_FLAG, True)
    return handler


def _find_managed_structured_handler(root_logger: logging.Logger) -> logging.Handler | None:
    for handler in root_logger.handlers:
        if _is_managed_structured_handler(handler):
            return handler
    return None


def configure_structured_logging(level: int) -> None:
    """
    Configure root logger to emit JSON logs preserving ``extra`` fields.

    This configuration is additive and idempotent:
    - existing handlers are preserved;
    - only one managed structured stdout handler is maintained;
    - repeated calls update the managed handler instead of duplicating it.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = _find_managed_structured_handler(root_logger)
    if handler is None:
        handler = _build_managed_structured_handler(level)
        root_logger.addHandler(handler)
        return

    handler.setLevel(level)
    if not isinstance(handler.formatter, CloudJsonFormatter):
        handler.setFormatter(CloudJsonFormatter())