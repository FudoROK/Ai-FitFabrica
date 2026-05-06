"""Canonical CRM write policy and payload shaping rules."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.domain.crm.profile import build_crm_profile_from_lead
from src.adapters.factories import get_crm_adapter


ROLLING_SUMMARY_FIELDS: tuple[str, ...] = ("rolling_summary", "sf_rolling_summary")


def _is_blank_string(value: object) -> bool:
    return isinstance(value, str) and not value.strip()


def build_profile_sync_payload(*, lead, existing_properties: Mapping[str, object] | None = None) -> dict[str, object]:
    crm = get_crm_adapter()
    canonical_profile = build_crm_profile_from_lead(lead)
    raw_payload = crm.build_profile_properties(profile=canonical_profile, existing_properties=existing_properties)
    return normalize_crm_write_properties(
        properties=raw_payload,
        allowed_fields=crm.profile_property_names(),
    )


def normalize_crm_write_properties(
    *,
    properties: Mapping[str, Any],
    allowed_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Normalize outgoing CRM properties for safe writes.

    Rules:
    - keep only allowlisted keys when ``allowed_fields`` is provided;
    - drop values equal to ``None``;
    - drop blank strings;
    - drop empty rolling summary values explicitly.
    """
    allowed = set(allowed_fields or ())
    use_allowlist = bool(allowed)

    normalized: dict[str, Any] = {}
    for key, value in properties.items():
        if use_allowlist and key not in allowed:
            continue
        if value is None:
            continue
        if _is_blank_string(value):
            continue
        if key in ROLLING_SUMMARY_FIELDS and _is_blank_string(value):
            continue
        normalized[key] = value
    return normalized
