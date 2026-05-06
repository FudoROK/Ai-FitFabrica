from __future__ import annotations

from datetime import date, datetime
from typing import Any


def normalize_memory_payload_for_json(value: Any) -> Any:
    """Recursively normalize memory-agent payload values to JSON-safe primitives."""
    if isinstance(value, dict):
        return {key: normalize_memory_payload_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_memory_payload_for_json(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()

    firestore_datetime = _coerce_firestore_timestamp_like(value)
    if firestore_datetime is not None:
        return firestore_datetime.isoformat()

    return value


def _coerce_firestore_timestamp_like(value: Any) -> datetime | None:
    """Convert Firestore timestamp-like objects to datetime when possible."""
    to_datetime = getattr(value, "to_datetime", None)
    if callable(to_datetime):
        converted = to_datetime()
        if isinstance(converted, datetime):
            return converted

    to_datetime_pascal = getattr(value, "ToDatetime", None)
    if callable(to_datetime_pascal):
        converted = to_datetime_pascal()
        if isinstance(converted, datetime):
            return converted

    return None
