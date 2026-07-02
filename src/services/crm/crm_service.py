"""Vendor-agnostic CRM provider facade (canonical CRM boundary)."""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from src.adapters.factories import get_crm_adapter
from src.settings import load_settings
from .crm_write_policy import normalize_crm_write_properties

logger = logging.getLogger(__name__)


def _crm():
    return get_crm_adapter()


def crm_provider() -> str:
    return load_settings().crm_provider


def crm_sync_enabled() -> bool:
    return load_settings().crm_sync_enabled


def crm_profile_sync_enabled() -> bool:
    return load_settings().crm_profile_sync_enabled

def crm_enabled() -> bool:
    return _crm().is_enabled()


def find_contact_ref_by_external_identity(*, channel: str, external_user_id: str) -> Optional[str]:
    normalized_channel = (channel or "telegram").strip().lower()
    normalized_external_user_id = str(external_user_id or "").strip()
    if not normalized_external_user_id:
        return None
    if not crm_sync_enabled() or not crm_enabled():
        return None
    try:
        return _crm().find_contact(external_user_id=normalized_external_user_id)
    except Exception:  # pragma: no cover
        logger.exception(
            "CRM contact lookup failed",
            extra={"channel": normalized_channel, "external_user_id": normalized_external_user_id},
        )
        return None


def find_contact_ref_by_channel_user_id(channel_user_id: str) -> Optional[str]:
    return find_contact_ref_by_external_identity(channel="telegram", external_user_id=channel_user_id)


def create_contact_for_external_identity(
    *,
    channel: str,
    external_user_id: str,
    first_name_hint: Optional[str] = None,
) -> Optional[str]:
    normalized_channel = (channel or "telegram").strip().lower()
    normalized_external_user_id = str(external_user_id or "").strip()
    if not normalized_external_user_id:
        return None
    if not crm_sync_enabled() or not crm_enabled():
        return None
    try:
        contact_ref = _crm().create_contact(
            external_user_id=normalized_external_user_id,
            first_name=first_name_hint,
        )
        return str(contact_ref or "").strip() or None
    except Exception:  # pragma: no cover
        logger.exception(
            "CRM contact create failed",
            extra={"channel": normalized_channel, "external_user_id": normalized_external_user_id},
        )
        return None


def create_contact_for_telegram_id(*, telegram_user_id: str, first_name_hint: Optional[str] = None) -> Optional[str]:
    return create_contact_for_external_identity(
        channel="telegram",
        external_user_id=telegram_user_id,
        first_name_hint=first_name_hint,
    )


def load_contact_profile(contact_ref: str) -> dict[str, str]:
    default_profile = {"firstname": "", "telegram_user_id": "", "niche": "", "pain_points": "", "need_solution": ""}
    if not contact_ref or not crm_sync_enabled() or not crm_enabled():
        return default_profile

    property_names = _crm().profile_property_names()
    if not property_names:
        return default_profile

    payload = _crm().get_contact(contact_id=contact_ref, properties=property_names)
    if not payload:
        return default_profile
    properties = payload.get("properties", {})
    return {property_name: properties.get(property_name) or "" for property_name in property_names}


def update_contact_properties(
    *,
    contact_ref: str,
    properties: dict[str, object],
    allowed_fields: Sequence[str] | None = None,
) -> bool:
    normalized = normalize_crm_write_properties(properties=properties, allowed_fields=allowed_fields)
    if not contact_ref or not normalized:
        return False
    if not crm_sync_enabled() or not crm_enabled():
        return False
    try:
        _crm().update_contact(contact_id=contact_ref, properties=normalized)
        return True
    except Exception:  # pragma: no cover
        logger.exception("CRM contact update failed", extra={"contact_ref": contact_ref})
        return False


def update_contact_memory(
    *,
    contact_ref: str,
    daily_text: Optional[str],
    daily_date: Optional[str],
    rolling_text: Optional[str],
    rolling_version: Optional[int],
    rolling_hash: Optional[str],
) -> bool:
    memory_allowed_fields = _crm().memory_property_names()
    properties = _crm().memory_properties(
        daily_text=daily_text,
        daily_date=daily_date,
        rolling_text=rolling_text,
        rolling_version=rolling_version,
        rolling_hash=rolling_hash,
    )
    return update_contact_properties(
        contact_ref=contact_ref,
        properties=properties,
        allowed_fields=memory_allowed_fields,
    )
