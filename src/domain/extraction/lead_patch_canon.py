from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo

LEAD_PATCH_STRING_FIELDS: tuple[str, ...] = (
    "first_name",
    "full_name",
    "business_type",
    "business_description",
    "budget_hint",
)
LEAD_PATCH_LIST_FIELDS: tuple[str, ...] = ("pain_points", "needs")
LEAD_PATCH_LOCATION_FIELDS: tuple[str, ...] = ("city", "country")
LEAD_PATCH_TIMEZONE_FIELDS: tuple[str, ...] = ("timezone",)
LEAD_PATCH_SUPPORTED_FIELDS: tuple[str, ...] = (
    *LEAD_PATCH_STRING_FIELDS,
    *LEAD_PATCH_LIST_FIELDS,
    *LEAD_PATCH_LOCATION_FIELDS,
    *LEAD_PATCH_TIMEZONE_FIELDS,
)

_PLACEHOLDER_STRINGS = {
    "-",
    "—",
    "unknown",
    "n/a",
    "na",
    "none",
    "null",
    "?",
    "не знаю",
    "нет",
}


def _is_placeholder_string(value: str) -> bool:
    return value.strip().casefold() in _PLACEHOLDER_STRINGS


def _is_valid_iana_timezone(value: str) -> bool:
    try:
        ZoneInfo(value)
    except Exception:
        return False
    return "/" in value


def extract_raw_lead_patch(raw_payload: Any) -> dict[str, Any]:
    """Extract lead patch data from compatibility payload shapes."""
    if not isinstance(raw_payload, dict):
        return {}

    raw_profile_patch: dict[str, Any] = {}
    nested_profile = raw_payload.get("lead_profile")
    if isinstance(nested_profile, dict):
        raw_profile_patch.update(nested_profile)

    for field in LEAD_PATCH_SUPPORTED_FIELDS:
        if field in raw_payload:
            raw_profile_patch[field] = raw_payload.get(field)

    return raw_profile_patch


def _normalize_string(value: Any) -> str | None:
    if value is None or not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or _is_placeholder_string(normalized):
        return None
    return normalized


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def canonicalize_lead_patch(raw_patch: Any) -> dict[str, Any]:
    if not isinstance(raw_patch, dict):
        return {}

    canonical: dict[str, Any] = {}

    for field in (*LEAD_PATCH_STRING_FIELDS, *LEAD_PATCH_LOCATION_FIELDS):
        value = _normalize_string(raw_patch.get(field))
        if value is not None:
            canonical[field] = value

    timezone_value = _normalize_string(raw_patch.get("timezone"))
    if timezone_value and _is_valid_iana_timezone(timezone_value):
        canonical["timezone"] = timezone_value

    for field in LEAD_PATCH_LIST_FIELDS:
        values = _normalize_string_list(raw_patch.get(field))
        if values:
            canonical[field] = values

    return canonical


def apply_lead_patch(existing_profile: Any, canonical_patch: Any) -> dict[str, Any]:
    profile = dict(existing_profile) if isinstance(existing_profile, dict) else {}
    patch = canonical_patch if isinstance(canonical_patch, dict) else {}

    for field in LEAD_PATCH_STRING_FIELDS:
        value = patch.get(field)
        if isinstance(value, str) and value:
            profile[field] = value

    for field in LEAD_PATCH_LIST_FIELDS:
        incoming = patch.get(field)
        if not isinstance(incoming, list) or not incoming:
            continue

        existing_values = profile.get(field)
        merged: list[str] = []
        seen: set[str] = set()

        if isinstance(existing_values, list):
            for item in existing_values:
                if not isinstance(item, str):
                    continue
                cleaned = item.strip()
                if not cleaned or cleaned in seen:
                    continue
                seen.add(cleaned)
                merged.append(cleaned)

        for item in incoming:
            if not isinstance(item, str):
                continue
            cleaned = item.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            merged.append(cleaned)

        if merged:
            profile[field] = merged

    for field in (*LEAD_PATCH_LOCATION_FIELDS, *LEAD_PATCH_TIMEZONE_FIELDS):
        value = patch.get(field)
        if isinstance(value, str) and value:
            profile[field] = value

    return profile


def compose_lead_update_payload(raw_payload: Any, existing_profile: Any) -> dict[str, Any]:
    """Build Firestore lead update payload with canonical lead_profile semantics."""
    payload = raw_payload if isinstance(raw_payload, dict) else {}

    passthrough: dict[str, Any] = {}
    for key, value in payload.items():
        if key == "lead_profile" or key in LEAD_PATCH_SUPPORTED_FIELDS:
            continue
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        passthrough[key] = value

    canonical_profile_patch = canonicalize_lead_patch(extract_raw_lead_patch(payload))
    for field in (*LEAD_PATCH_LOCATION_FIELDS, *LEAD_PATCH_TIMEZONE_FIELDS):
        value = canonical_profile_patch.get(field)
        if isinstance(value, str) and value:
            passthrough[field] = value

    canonical_profile_patch = {
        key: value
        for key, value in canonical_profile_patch.items()
        if key in LEAD_PATCH_STRING_FIELDS or key in LEAD_PATCH_LIST_FIELDS
    }

    if canonical_profile_patch:
        passthrough["lead_profile"] = apply_lead_patch(existing_profile, canonical_profile_patch)

    return passthrough
