"""Async-facing Firestore lead repository facade."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.domain.models import Lead
from src.services.inbound.lead_patch_preparation_service import LeadPatchPreparationService

from .firestore_lead_persistence import (
    FirestoreLeadCoreRepository,
    FirestoreLeadCrmBindingRepository,
    FirestoreLeadExtractionAttemptsRepository,
    FirestoreLeadMessagesRepository,
    FirestoreLeadPatchRepository,
    apply_lead_patch as storage_apply_lead_patch,
    get_lead_by_id as storage_get_lead_by_id,
)


class FirestoreLeadRepository:
    """Application-facing lead persistence facade composed from narrow repositories."""

    def __init__(
        self,
        *,
        core_repo: Optional[FirestoreLeadCoreRepository] = None,
        patch_repo: Optional[FirestoreLeadPatchRepository] = None,
        patch_preparation_service: Optional[LeadPatchPreparationService] = None,
        messages_repo: Optional[FirestoreLeadMessagesRepository] = None,
        crm_binding_repo: Optional[FirestoreLeadCrmBindingRepository] = None,
        extraction_attempts_repo: Optional[FirestoreLeadExtractionAttemptsRepository] = None,
    ) -> None:
        self.core_repo = core_repo or FirestoreLeadCoreRepository(get_lead_by_id_fn=storage_get_lead_by_id)
        self.patch_repo = patch_repo or FirestoreLeadPatchRepository(apply_patch_fn=storage_apply_lead_patch)
        self.patch_preparation_service = patch_preparation_service or LeadPatchPreparationService()
        self.messages_repo = messages_repo or FirestoreLeadMessagesRepository()
        self.crm_binding_repo = crm_binding_repo or FirestoreLeadCrmBindingRepository()
        self.extraction_attempts_repo = extraction_attempts_repo or FirestoreLeadExtractionAttemptsRepository()

    async def get(self, lead_id: Optional[str]) -> Optional[Lead]:
        return await self.core_repo.get(lead_id)

    async def get_or_create_canonical(
        self,
        *,
        canonical_lead_id: str,
        channel: str,
        external_user_id: str | int | None,
        username: Optional[str],
        first_name: Optional[str],
    ) -> Lead:
        return await self.core_repo.get_or_create_canonical(
            canonical_lead_id=canonical_lead_id,
            channel=channel,
            external_user_id=external_user_id,
            username=username,
            first_name=first_name,
        )

    async def save(self, lead: Lead) -> None:
        await self.core_repo.save(lead)

    async def apply_lead_profile(self, lead_id: Optional[str], profile: dict[str, object]) -> bool:
        return await self.apply_lead_patch(lead_id, {"lead_profile": profile or {}})

    async def apply_lead_patch(self, lead_id: Optional[str], lead_patch: dict[str, object]) -> bool:
        if not lead_id:
            return False
        existing_lead = await self.core_repo.get(str(lead_id))
        canonical_payload = self.patch_preparation_service.compose(
            lead_patch=dict(lead_patch or {}),
            existing_lead=existing_lead,
        )
        if not canonical_payload:
            return True

        applied = await self.patch_repo.apply_canonical_patch(str(lead_id), canonical_payload)
        return applied

    async def update_last_activity(self, lead_id: Optional[str], activity_at: datetime) -> bool:
        return await self.core_repo.update_last_activity(lead_id, activity_at)

    async def record_extraction_attempt(self, *, lead_id: Optional[str], attempt: dict[str, object]) -> bool:
        return await self.extraction_attempts_repo.record_extraction_attempt(lead_id=lead_id, attempt=attempt)

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
        return await self.messages_repo.append_message(
            lead_id=lead_id,
            role=role,
            text=text,
            timestamp=timestamp,
            channel=channel,
            chat_id=chat_id,
            external_user_id=external_user_id,
            message_idempotency_key=message_idempotency_key,
        )

    async def fetch_last_messages(self, *, lead_id: str, since: datetime, limit: int = 30) -> list[dict]:
        return await self.messages_repo.fetch_last_messages(lead_id=lead_id, since=since, limit=limit)

    async def get_messages_in_window(
        self,
        *,
        lead_id: str,
        start_utc: datetime,
        end_utc: datetime,
        limit: int = 200,
    ) -> list[dict]:
        return await self.messages_repo.get_messages_in_window(
            lead_id=lead_id,
            start_utc=start_utc,
            end_utc=end_utc,
            limit=limit,
        )

    async def upsert_hubspot_contact_id(self, *, lead_id: str, contact_id: str) -> bool:
        return await self.crm_binding_repo.upsert_hubspot_contact_id(lead_id=lead_id, contact_id=contact_id)

    async def upsert_crm_contact_binding(
        self,
        *,
        lead_id: str,
        crm_contact_ref: str,
        crm_provider: str = "hubspot",
    ) -> bool:
        return await self.crm_binding_repo.upsert_crm_contact_binding(
            lead_id=lead_id,
            crm_contact_ref=crm_contact_ref,
            crm_provider=crm_provider,
        )
