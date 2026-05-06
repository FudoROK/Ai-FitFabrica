from __future__ import annotations

from typing import Any


def _clean_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_crm_profile_from_lead(lead: Any) -> dict[str, str | list[str]]:
    """Build the minimal CRM payload for the skeleton baseline."""

    lead_profile = getattr(lead, "lead_profile", None)
    profile = lead_profile if isinstance(lead_profile, dict) else {}

    return {
        "first_name": _clean_string(getattr(lead, "first_name", None)) or _clean_string(profile.get("first_name")),
    }
