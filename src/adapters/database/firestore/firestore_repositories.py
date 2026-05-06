"""Async-facing Firestore repository façades."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from src.domain.models import ChatSession, Lead
from src.memory_layer import MemoryLayerService
from src.adapters.database.firestore.storage_primitives import get_or_create_chat_session, update_chat_session
from src.adapters.database.firestore.firestore_async_executor import run_blocking
from .firestore_lead_persistence import (
    FirestoreLeadCoreRepository,
    FirestoreLeadCrmBindingRepository,
    FirestoreLeadExtractionAttemptsRepository,
    FirestoreLeadMessagesRepository,
    FirestoreLeadPatchRepository,
    FirestoreLeadSummariesRepository,
    apply_lead_patch as storage_apply_lead_patch,
    get_lead_by_id as storage_get_lead_by_id,
)
from src.services.inbound.lead_patch_preparation_service import LeadPatchPreparationService

logger = logging.getLogger(__name__)


class FirestoreLeadRepository:
    """Application-facing lead persistence façade composed from narrow repositories."""

    def __init__(
        self,
        *,
        core_repo: Optional[FirestoreLeadCoreRepository] = None,
        patch_repo: Optional[FirestoreLeadPatchRepository] = None,
        patch_preparation_service: Optional[LeadPatchPreparationService] = None,
        memory_layer_service: Optional[MemoryLayerService] = None,
        messages_repo: Optional[FirestoreLeadMessagesRepository] = None,
        summaries_repo: Optional[FirestoreLeadSummariesRepository] = None,
        crm_binding_repo: Optional[FirestoreLeadCrmBindingRepository] = None,
        extraction_attempts_repo: Optional[FirestoreLeadExtractionAttemptsRepository] = None,
    ) -> None:
        self.core_repo = core_repo or FirestoreLeadCoreRepository(get_lead_by_id_fn=storage_get_lead_by_id)
        self.patch_repo = patch_repo or FirestoreLeadPatchRepository(apply_patch_fn=storage_apply_lead_patch)
        self.patch_preparation_service = patch_preparation_service or LeadPatchPreparationService()
        self.memory_layer_service = memory_layer_service
        self.messages_repo = messages_repo or FirestoreLeadMessagesRepository()
        self.summaries_repo = summaries_repo or FirestoreLeadSummariesRepository()
        self.crm_binding_repo = crm_binding_repo or FirestoreLeadCrmBindingRepository()
        self.extraction_attempts_repo = (
            extraction_attempts_repo or FirestoreLeadExtractionAttemptsRepository()
        )

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
        await self._sync_active_window_timezone_if_needed(
            lead_id=str(lead_id),
            existing_lead=existing_lead,
            canonical_payload=canonical_payload,
            lead_updated=applied,
        )
        return applied

    async def _sync_active_window_timezone_if_needed(
        self,
        *,
        lead_id: str,
        existing_lead: Optional[Lead],
        canonical_payload: dict[str, object],
        lead_updated: bool,
    ) -> None:
        if self.memory_layer_service is None:
            logger.info(
                "active_window_timezone_sync_skipped",
                extra={"lead_id": lead_id, "reason": "memory_layer_service_not_configured"},
            )
            return

        if not lead_updated:
            logger.info(
                "active_window_timezone_sync_skipped",
                extra={"lead_id": lead_id, "reason": "lead_timezone_not_updated"},
            )
            return

        new_timezone = canonical_payload.get("timezone")
        if not isinstance(new_timezone, str) or not new_timezone.strip():
            logger.info(
                "active_window_timezone_sync_skipped",
                extra={"lead_id": lead_id, "reason": "lead_timezone_not_updated"},
            )
            return
        new_timezone = new_timezone.strip()

        previous_timezone = (
            existing_lead.timezone.strip()
            if existing_lead and isinstance(existing_lead.timezone, str) and existing_lead.timezone.strip()
            else None
        )
        if previous_timezone == new_timezone:
            logger.info(
                "active_window_timezone_sync_skipped",
                extra={"lead_id": lead_id, "reason": "timezone_unchanged"},
            )
            return

        await self.memory_layer_service.sync_active_window_timezone(
            lead_id=lead_id,
            timezone_name=new_timezone,
            updated_at=datetime.now(tz=timezone.utc),
        )

    async def update_last_activity(self, lead_id: Optional[str], activity_at: datetime) -> bool:
        return await self.core_repo.update_last_activity(lead_id, activity_at)

    async def record_extraction_attempt(self, *, lead_id: Optional[str], attempt: dict[str, object]) -> bool:
        return await self.extraction_attempts_repo.record_extraction_attempt(
            lead_id=lead_id,
            attempt=attempt,
        )

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

    async def fetch_last_messages(
        self,
        *,
        lead_id: str,
        since: datetime,
        limit: int = 30,
    ) -> list[dict]:
        return await self.messages_repo.fetch_last_messages(
            lead_id=lead_id,
            since=since,
            limit=limit,
        )

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
        return await self.crm_binding_repo.upsert_hubspot_contact_id(
            lead_id=lead_id,
            contact_id=contact_id,
        )

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

    async def fetch_daily_summary(self, *, lead_id: str, memory_day_key: str) -> Optional[dict]:
        return await self.summaries_repo.fetch_daily_summary(
            lead_id=lead_id,
            memory_day_key=memory_day_key,
        )

    async def fetch_latest_daily_summary(self, *, lead_id: str) -> Optional[dict]:
        return await self.summaries_repo.fetch_latest_daily_summary(lead_id=lead_id)

    async def write_daily_summary(
        self,
        *,
        lead_id: str,
        memory_day_key: str,
        summary_text: str,
        open_questions: list[str],
        carry_forward_notes: list[str],
        learned_facts: list[str],
        changed_facts: list[str],
        memory_relevance_flags: list[str],
        created_at: datetime,
        messages_used_count: Optional[int] = None,
        source_window_start: Optional[datetime] = None,
        source_window_end: Optional[datetime] = None,
    ) -> bool:
        return await self.summaries_repo.write_daily_summary(
            lead_id=lead_id,
            memory_day_key=memory_day_key,
            summary_text=summary_text,
            open_questions=open_questions,
            carry_forward_notes=carry_forward_notes,
            learned_facts=learned_facts,
            changed_facts=changed_facts,
            memory_relevance_flags=memory_relevance_flags,
            created_at=created_at,
            messages_used_count=messages_used_count,
            source_window_start=source_window_start,
            source_window_end=source_window_end,
        )

    async def acquire_memory_write_guard(
        self,
        *,
        lead_id: str,
        idempotency_key: str,
        created_at: datetime,
    ) -> bool:
        return await self.summaries_repo.acquire_memory_write_guard(
            lead_id=lead_id,
            idempotency_key=idempotency_key,
            created_at=created_at,
        )

    async def release_memory_write_guard(self, *, lead_id: str, idempotency_key: str) -> None:
        await self.summaries_repo.release_memory_write_guard(
            lead_id=lead_id,
            idempotency_key=idempotency_key,
        )

    async def fetch_rolling_summary(self, *, lead_id: str) -> Optional[dict]:
        return await self.summaries_repo.fetch_rolling_summary(lead_id=lead_id)

    async def create_rolling_artifact(
        self,
        *,
        lead_id: str,
        artifact_id: str,
        artifact_payload: dict[str, object],
    ) -> bool:
        return await self.summaries_repo.create_rolling_artifact(
            lead_id=lead_id,
            artifact_id=artifact_id,
            artifact_payload=artifact_payload,
        )

    async def promote_rolling_pointer(
        self,
        *,
        lead_id: str,
        artifact_id: str,
        pointer_payload: dict[str, object],
    ) -> bool:
        return await self.summaries_repo.promote_rolling_pointer(
            lead_id=lead_id,
            artifact_id=artifact_id,
            pointer_payload=pointer_payload,
        )

    async def fetch_current_rolling_pointer(self, *, lead_id: str) -> Optional[dict]:
        return await self.summaries_repo.fetch_current_rolling_pointer(lead_id=lead_id)

    async def fetch_rolling_artifact(self, *, lead_id: str, artifact_id: str) -> Optional[dict]:
        return await self.summaries_repo.fetch_rolling_artifact(lead_id=lead_id, artifact_id=artifact_id)

    async def update_rolling_summary(
        self,
        *,
        lead_id: str,
        rolling_update: dict[str, object],
        updated_at: datetime,
    ) -> bool:
        return await self.summaries_repo.update_rolling_summary(
            lead_id=lead_id,
            rolling_update=rolling_update,
            updated_at=updated_at,
        )


class FirestoreSessionRepository:
    """Persist chat sessions in Firestore only."""

    async def get_or_create(
        self,
        *,
        channel: str,
        chat_id: str | int | None,
        external_user_id: str | int | None,
        lead_id: Optional[str],
    ) -> ChatSession:
        firestore_session = await run_blocking(
            get_or_create_chat_session,
            channel,
            str(external_user_id or chat_id),
            username=None,
        )
        if not firestore_session:
            raise RuntimeError("Firestore is unavailable: failed to get or create chat session")
        firestore_session.lead_id = lead_id or firestore_session.lead_id
        firestore_session.chat_id = str(chat_id) if chat_id is not None else firestore_session.chat_id
        firestore_session.channel = firestore_session.channel or channel
        firestore_session.external_user_id = firestore_session.external_user_id or str(
            external_user_id or chat_id
        )
        return firestore_session

    async def get(self, session_id: str) -> Optional[ChatSession]:
        if not session_id or ":" not in session_id:
            return None
        channel, external_user_id = session_id.split(":", 1)
        session = await run_blocking(get_or_create_chat_session, channel, external_user_id, username=None)
        if not session:
            raise RuntimeError("Firestore is unavailable: failed to fetch chat session")
        return session

    async def save(self, session: ChatSession) -> None:
        if not session or not session.id:
            return
        await run_blocking(update_chat_session, session)


__all__ = [
    "FirestoreLeadRepository",
    "FirestoreSessionRepository",
]
