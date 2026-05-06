from __future__ import annotations

import time

from ...utils.log_redaction import redact
from ..core.errors import (
    ERROR_AUTH,
    ERROR_BAD_REQUEST,
    ERROR_INVALID_OUTPUT,
    ERROR_RATE_LIMITED,
    ERROR_TIMEOUT,
    classify_exception,
    classify_http_status,
)
from ..core.result import LLMResult
from ..core.types import LLMError


def classify_provider_exception(
    *,
    exc: Exception,
    started: float,
    retry_count: int,
    model: str,
    provider_name: str,
) -> LLMResult:
    http_status = extract_http_status(exc)
    error_type = classify_http_status(http_status) if http_status is not None else classify_exception(exc)
    if isinstance(exc, ValueError):
        error_type = ERROR_INVALID_OUTPUT
    retriable = error_type in {ERROR_TIMEOUT, ERROR_RATE_LIMITED}
    if error_type in {ERROR_AUTH, ERROR_BAD_REQUEST, ERROR_INVALID_OUTPUT}:
        retriable = False
    return build_error_result(
        started=started,
        retry_count=retry_count,
        model=model,
        provider_name=provider_name,
        error_type=error_type,
        message=redact(str(exc)),
        retriable=retriable,
        http_status=http_status,
    )


def build_error_result(
    *,
    started: float,
    retry_count: int,
    model: str,
    provider_name: str,
    error_type: str,
    message: str,
    retriable: bool,
    http_status: int | None = None,
) -> LLMResult:
    return LLMResult(
        status="error",
        provider=provider_name,
        model=model,
        latency_ms=int((time.perf_counter() - started) * 1000),
        retry_count=retry_count,
        usage=None,
        error=LLMError(
            type=error_type,
            message_redacted=redact(message),
            retriable=retriable,
            http_status=http_status,
        ),
    )


def extract_http_status(exc: Exception) -> int | None:
    for attr in ("status_code", "http_status", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    code = getattr(response, "status_code", None)
    return code if isinstance(code, int) else None
