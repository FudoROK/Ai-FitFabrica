"""Narrow Firestore persistence surfaces for lead-related data."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.domain.models import Lead
from src.adapters.database.firestore.storage_primitives import (
    apply_lead_patch,
    create_or_get_canonical_lead,
    fetch_messages_in_window,
    fetch_recent_messages,
    get_lead_by_id,
    update_lead,
    update_lead_activity,
    upsert_crm_contact_binding,
    write_extraction_attempt,
)
from src.adapters.database.firestore.message_store import _append_message_with_ttl_and_return_id
from src.adapters.database.firestore.firestore_async_executor import run_blocking


class FirestoreLeadCoreRepository:
    """Core lead retrieval and persistence."""

    def __init__(self, *, get_lead_by_id_fn=get_lead_by_id) -> None:
        self._get_lead_by_id = get_lead_by_id_fn

    async def get(self, lead_id: Optional[str]) -> Optional[Lead]:
        if not lead_id:
            return None
        return await run_blocking(self._get_lead_by_id, lead_id)

    async def get_or_create_canonical(
        self,
        *,
        canonical_lead_id: str,
        channel: str,
        external_user_id: str | int | None,
        username: Optional[str],
        first_name: Optional[str],
    ) -> Lead:
        created = await run_blocking(
            create_or_get_canonical_lead,
            canonical_lead_id=str(canonical_lead_id),
            channel=channel,
            external_user_id=str(external_user_id or ""),
            username=username,
            first_name=first_name,
        )
        if not created:
            raise RuntimeError("Firestore is unavailable: failed to create canonical lead")
        return created

    async def save(self, lead: Lead) -> None:
        if not lead or not lead.lead_id:
            return
        await run_blocking(update_lead, lead)

    async def update_last_activity(self, lead_id: Optional[str], activity_at: datetime) -> bool:
        if not lead_id:
            return False
        return await run_blocking(update_lead_activity, str(lead_id), activity_at)


class FirestoreLeadPatchRepository:
    """Persist canonical lead patches only."""

    def __init__(self, *, apply_patch_fn=apply_lead_patch) -> None:
        self._apply_patch = apply_patch_fn

    async def apply_canonical_patch(self, lead_id: Optional[str], canonical_patch: dict[str, object]) -> bool:
        if not lead_id or not canonical_patch:
            return False
        return await run_blocking(self._apply_patch, str(lead_id), canonical_patch)


class FirestoreLeadMessagesRepository:
    """Lead messages persistence and reads."""

    async def append_message(
        self,
        *,
        lead_id: str,
        role: str,
        text: str,
        timestamp: datetime,
        channel: Optional[str],
        chat_id: Optional[str],
        external_user_id: Optional[str],
        message_idempotency_key: Optional[str] = None,
    ) -> str | None:
        return await run_blocking(
            _append_message_with_ttl_and_return_id,
            lead_id=lead_id,
            role=role,
            text=text,
            timestamp=timestamp,
            channel=channel,
            chat_id=chat_id,
            external_user_id=external_user_id,
            message_idempotency_key=message_idempotency_key,
        )

    async def fetch_last_messages(
        self,
        *,
        lead_id: str,
        since: datetime,
        limit: int = 30,
    ) -> list[dict]:
        return await run_blocking(fetch_recent_messages, lead_id, since=since, limit=limit)

    async def get_messages_in_window(
        self,
        *,
        lead_id: str,
        start_utc: datetime,
        end_utc: datetime,
        limit: int = 200,
    ) -> list[dict]:
        return await run_blocking(
            fetch_messages_in_window,
            lead_id=lead_id,
            start_utc=start_utc,
            end_utc=end_utc,
            limit=limit,
        )


class FirestoreLeadCrmBindingRepository:
    """CRM binding persistence for leads."""

    async def upsert_crm_contact_binding(
        self,
        *,
        lead_id: str,
        crm_contact_ref: str,
        crm_provider: str = "hubspot",
    ) -> bool:
        return await run_blocking(
            upsert_crm_contact_binding,
            lead_id=lead_id,
            crm_contact_ref=crm_contact_ref,
            crm_provider=crm_provider,
        )


class FirestoreLeadExtractionAttemptsRepository:
    """Extraction-attempt audit persistence."""

    async def record_extraction_attempt(self, *, lead_id: Optional[str], attempt: dict[str, object]) -> bool:
        if not lead_id:
            return False
        return await run_blocking(write_extraction_attempt, str(lead_id), attempt)
