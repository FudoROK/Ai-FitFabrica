from __future__ import annotations

from typing import Mapping, Optional

HUBSPOT_PROFILE_FIELD_MAPPING: tuple[tuple[str, str], ...] = (
    ("first_name", "firstname"),
)


MEMORY_ROLLING_SUMMARY_LIMIT = 8000
HUBSPOT_MEMORY_PROPERTY_NAMES: tuple[str, ...] = (
    "sf_daily_summary_latest",
    "sf_rolling_summary",
)


def _clean_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_hubspot_value(field: str, value: object) -> str:
    _ = field
    return _clean_string(value)


def build_contact_properties(
    profile: Mapping[str, object],
    *,
    existing_properties: Mapping[str, object] | None = None,
) -> dict[str, str]:
    payload: dict[str, str] = {}

    for canonical_field, hubspot_property in HUBSPOT_PROFILE_FIELD_MAPPING:
        raw_value = profile.get(canonical_field)
        converted = _to_hubspot_value(canonical_field, raw_value)
        if converted:
            payload[hubspot_property] = converted

    if existing_properties:
        for property_name, value in existing_properties.items():
            cleaned = _clean_string(value)
            if property_name in payload or not cleaned:
                continue
            payload[property_name] = cleaned

    return payload


def _truncate_text(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(value) <= limit:
        return value
    trimmed = value[: max(limit - 1, 0)].rstrip()
    return f"{trimmed}…"


def build_memory_properties(
    *,
    daily_text: Optional[str],
    daily_date: Optional[str],
    rolling_text: Optional[str],
    rolling_version: Optional[int],
    rolling_hash: Optional[str],
) -> dict[str, object]:
    _ = daily_date
    _ = rolling_version
    _ = rolling_hash
    properties: dict[str, object] = {}
    if daily_text and daily_text.strip():
        properties["sf_daily_summary_latest"] = daily_text
    if rolling_text and rolling_text.strip():
        properties["sf_rolling_summary"] = _truncate_text(rolling_text, MEMORY_ROLLING_SUMMARY_LIMIT)
    return properties
