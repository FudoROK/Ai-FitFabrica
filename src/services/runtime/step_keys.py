"""Canonical step keys for side-effect idempotency."""
from __future__ import annotations


class StepKeys:
    """Central registry for all side-effect processing steps."""

    SEND_REPLY = "send_reply"
    CRM_FIND_OR_CREATE_CONTACT = "crm_find_or_create_contact"
    CRM_BIND_CONTACT_REF = "crm_bind_contact_ref"
    CRM_UPDATE_CONTACT_PROFILE = "crm_update_contact_profile"
    CRM_SYNC_MEMORY = "crm_sync_memory"

    @staticmethod
    def send_reply(*, channel: str) -> str:
        normalized_channel = str(channel or "").strip().lower()
        return f"{normalized_channel}_send_reply"
