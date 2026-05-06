from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

ERROR_TIMEOUT = "timeout"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_AUTH = "auth_error"
ERROR_BAD_REQUEST = "bad_request"
ERROR_INVALID_OUTPUT = "invalid_output"
ERROR_UPSTREAM = "upstream_error"
ERROR_UNKNOWN = "unknown"


_HTTP_ERROR_MAP: dict[int, str] = {
    400: ERROR_BAD_REQUEST,
    401: ERROR_AUTH,
    403: ERROR_AUTH,
    408: ERROR_TIMEOUT,
    422: ERROR_BAD_REQUEST,
    429: ERROR_RATE_LIMITED,
    500: ERROR_UPSTREAM,
    502: ERROR_UPSTREAM,
    503: ERROR_UPSTREAM,
    504: ERROR_TIMEOUT,
}


def classify_http_status(http_status: Optional[int]) -> str:
    if http_status is None:
        return ERROR_UNKNOWN
    if http_status in _HTTP_ERROR_MAP:
        return _HTTP_ERROR_MAP[http_status]
    if 500 <= http_status <= 599:
        return ERROR_UPSTREAM
    if 400 <= http_status <= 499:
        return ERROR_BAD_REQUEST
    return ERROR_UNKNOWN


def classify_exception(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()

    if isinstance(exc, TimeoutError) or "timeout" in name:
        return ERROR_TIMEOUT

    if "rate" in name and "limit" in name:
        return ERROR_RATE_LIMITED

    status = _extract_http_status(exc)
    if status is not None:
        return classify_http_status(status)

    return ERROR_UNKNOWN


def _extract_http_status(exc: Exception) -> Optional[int]:
    for attr in ("status_code", "http_status", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    if isinstance(exc, Mapping):
        status = exc.get("status")
        if isinstance(status, int):
            return status

    return None
