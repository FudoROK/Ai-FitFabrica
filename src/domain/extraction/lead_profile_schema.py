from __future__ import annotations

from typing import Any

from .lead_patch_canon import (
    LEAD_PATCH_SUPPORTED_FIELDS,
    apply_lead_patch,
    canonicalize_lead_patch,
)

CANONICAL_PATCH_KEYS = LEAD_PATCH_SUPPORTED_FIELDS


def normalize_patch_value(value: Any) -> Any:
    return value


def extract_patch(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    patch = payload.get("lead_patch")
    return canonicalize_lead_patch(patch)


def non_empty_patch(existing: dict[str, Any] | None, incoming: dict[str, Any] | None) -> dict[str, Any]:
    canonical_existing = canonicalize_lead_patch(existing or {})
    canonical_incoming = canonicalize_lead_patch(incoming or {})
    return apply_lead_patch(canonical_existing, canonical_incoming)
