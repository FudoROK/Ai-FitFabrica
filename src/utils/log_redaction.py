"""Helpers for safe logging and centralized secret redaction policy."""
from __future__ import annotations

import hashlib
import logging
import os
import re
from collections.abc import Mapping, Sequence
from typing import Any, Optional

_MASK = "***"
_LOG_RECORD_RESERVED_KEYS = set(logging.makeLogRecord({}).__dict__.keys())
_REDACTION_MARKER_ATTR = "_redaction_policy_applied"
_REDACTION_FACTORY_MARKER_ATTR = "_redaction_policy_factory_wrapped"

_BOT_TOKEN_PATTERN = re.compile(r"/bot[^/\s]+")
_BOT_API_PATTERN = re.compile(r"(bot)[0-9]{6,}:[A-Za-z0-9_-]{10,}", re.IGNORECASE)
_AUTH_BEARER_PATTERN = re.compile(r"(Authorization\s*:\s*Bearer\s+)[^\s,;]+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"(\bBearer\s+)[A-Za-z0-9._~+\-/]+=*", re.IGNORECASE)
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_GENERIC_TOKEN_PATTERN = re.compile(
    r"(?P<prefix>\b(?:token|access_token|refresh_token|id_token|api[_-]?key|client[_-]?secret|secret|password|webhook[_-]?secret|session[_-]?id)\b\s*[=:]\s*)(?P<secret>[^\s,;]+)",
    re.IGNORECASE,
)

_SENSITIVE_KEYWORDS = (
    "authorization",
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "client_secret",
    "private_key",
    "service_account",
    "session",
    "cookie",
)

_PII_FIELD_NAMES = {
    "email",
    "phone",
    "firstname",
    "lastname",
    "full_name",
    "first_name",
    "last_name",
    "address",
}

_SECRET_ENV_KEYS = (
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "CRM_ACCESS_TOKEN",
    "HUBSPOT_ACCESS_TOKEN",
    "HUBSPOT_PRIVATE_APP_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
)


def _looks_sensitive_key(key: object) -> bool:
    normalized = str(key or "").strip().lower().replace("-", "_")
    return any(word in normalized for word in _SENSITIVE_KEYWORDS)


def redact(text: object) -> str:
    """Redact sensitive fragments from arbitrary text."""
    value = "" if text is None else str(text)
    value = _BOT_TOKEN_PATTERN.sub("/bot***", value)
    value = _BOT_API_PATTERN.sub(r"\1***", value)
    value = _AUTH_BEARER_PATTERN.sub(r"\1***", value)
    value = _BEARER_PATTERN.sub(r"\1***", value)
    value = _JWT_PATTERN.sub(_MASK, value)
    value = _GENERIC_TOKEN_PATTERN.sub(lambda m: f"{m.group('prefix')}{_MASK}", value)

    for env_name in _SECRET_ENV_KEYS:
        secret = os.getenv(env_name)
        if secret:
            value = value.replace(secret, _MASK)
    return value


def redact_structure(value: Any, *, key_hint: str | None = None) -> Any:
    """Recursively redact potentially sensitive values while preserving structure."""
    if value is None:
        return None

    if isinstance(value, Mapping):
        sanitized: dict[Any, Any] = {}
        for item_key, item_value in value.items():
            if _looks_sensitive_key(item_key):
                sanitized[item_key] = _MASK
            elif str(item_key).strip().lower() in _PII_FIELD_NAMES:
                sanitized[item_key] = _MASK
            else:
                sanitized[item_key] = redact_structure(item_value, key_hint=str(item_key))
        return sanitized

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_structure(item, key_hint=key_hint) for item in value]

    if _looks_sensitive_key(key_hint) or str(key_hint or "").strip().lower() in _PII_FIELD_NAMES:
        return _MASK

    if isinstance(value, (str, bytes, bytearray)):
        text = value.decode("utf-8", errors="replace") if isinstance(value, (bytes, bytearray)) else value
        return redact(text)

    if isinstance(value, (bool, int, float)):
        return value

    return redact(value)


class RedactingLogFilter(logging.Filter):
    """Logging filter that enforces centralized redaction on log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        _apply_redaction_to_record(record)
        return True


def install_redaction_logging_policy() -> None:
    """Install centralized redaction filter on root logger handlers."""
    _install_log_record_factory()

    root_logger = logging.getLogger()
    _ensure_filter_attached(root_logger)
    for handler in root_logger.handlers:
        _ensure_filter_attached(handler)


def _apply_redaction_to_record(record: logging.LogRecord) -> None:
    if getattr(record, _REDACTION_MARKER_ATTR, False):
        return

    record.msg = redact(record.msg)
    if record.args:
        if isinstance(record.args, tuple):
            record.args = tuple(redact_structure(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {k: redact_structure(v, key_hint=str(k)) for k, v in record.args.items()}
        else:
            record.args = redact_structure(record.args)

    for key, value in list(record.__dict__.items()):
        if key in _LOG_RECORD_RESERVED_KEYS:
            continue
        record.__dict__[key] = redact_structure(value, key_hint=key)

    if record.exc_info:
        exc_type, exc, _tb = record.exc_info
        if exc is not None:
            redacted_exc = Exception(redact(exc))
            record.exc_info = (exc_type, redacted_exc, None)

    setattr(record, _REDACTION_MARKER_ATTR, True)


def _install_log_record_factory() -> None:
    current_factory = logging.getLogRecordFactory()
    if getattr(current_factory, _REDACTION_FACTORY_MARKER_ATTR, False):
        return

    def _redacting_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = current_factory(*args, **kwargs)
        _apply_redaction_to_record(record)
        return record

    setattr(_redacting_factory, _REDACTION_FACTORY_MARKER_ATTR, True)
    logging.setLogRecordFactory(_redacting_factory)


def _ensure_filter_attached(target: logging.Filterer) -> None:
    has_filter = any(isinstance(item, RedactingLogFilter) for item in target.filters)
    if not has_filter:
        target.addFilter(RedactingLogFilter())


def hash_chat_id(chat_id: Optional[object]) -> Optional[str]:
    """Return a stable, non-reversible chat id hash for logs."""
    if chat_id is None:
        return None
    normalized = str(chat_id).strip()
    if not normalized:
        return None
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:12]
