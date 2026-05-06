"""Persistence/data-assembly helpers for memory sync orchestration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.domain.memory.rolling_content_policy import (
    RollingContentValidationResult,
    validate as validate_rolling_content,
)
from src.memory_layer import MemoryLayerService
from src.memory_layer.models import ConversationStateRecord
from .memory_summary_projection import build_lead_profile_payload, fetch_messages_for_window
from .memory_sync_repository_contract import MemorySyncLeadRepository

DAILY_SUMMARY_MESSAGE_LIMIT = 200


@dataclass
class LeadMemoryContext:
    lead_data: dict
    lead_profile: dict[str, str]
    rolling_summary: Optional[str]
    rolling_payload: dict | None
    active_window: dict
    conversation_state: dict


@dataclass
class DailySummaryWritePayload:
    memory_day_key: str
    summary_text: str
    open_questions: list[str]
    carry_forward_notes: list[str]
    learned_facts: list[str]
    changed_facts: list[str]
    memory_relevance_flags: list[str]
    created_at: datetime
    messages_used_count: int
    source_window_start: datetime
    source_window_end: datetime


@dataclass(frozen=True)
class ConfirmedRollingSummaryValidation:
    ok: bool
    reason_code: str | None
    normalized_text: str | None
    rolling_version: int | None
    rolling_hash: str | None


class MemorySyncPersistenceService:
    """Canonical persistence boundary for memory sync.

    Uses strict repository contract with no optional compatibility branches.
    """

    def __init__(
        self,
        *,
        leads_repo: MemorySyncLeadRepository,
        memory_layer_service: MemoryLayerService | None = None,
    ) -> None:
        self.leads_repo = leads_repo
        self.memory_layer_service = memory_layer_service

    async def load_lead_context(self, *, lead_id: str, include_rolling: bool = True) -> LeadMemoryContext:
        lead = await self.leads_repo.get(lead_id)
        lead_data = lead.model_dump(exclude_none=True) if lead else {}
        active_window: dict = {}
        conversation_state: dict = {}
        if self.memory_layer_service is not None:
            window = await self.memory_layer_service.get_active_window(lead_id=lead_id)
            state = await self.memory_layer_service.get_conversation_state(lead_id=lead_id)
            active_window = window.model_dump(mode="python", exclude_none=True) if window is not None else {}
            conversation_state = state.model_dump(mode="python", exclude_none=True) if state is not None else {}
        rolling_summary = None
        rolling_payload = None
        if include_rolling:
            rolling_payload = await self.leads_repo.fetch_rolling_summary(lead_id=lead_id)
            if isinstance(rolling_payload, dict):
                normalized_rolling_summary = self._normalize_rolling_summary_text(rolling_payload)
                if normalized_rolling_summary is not None:
                    rolling_summary = normalized_rolling_summary
                else:
                    rolling_payload = None
        return LeadMemoryContext(
            lead_data=lead_data,
            lead_profile=build_lead_profile_payload(lead_data),
            rolling_summary=rolling_summary,
            rolling_payload=rolling_payload if isinstance(rolling_payload, dict) else None,
            active_window=active_window,
            conversation_state=conversation_state,
        )

    @staticmethod
    def _validate_and_normalize_rolling_summary_text(rolling_payload: dict) -> RollingContentValidationResult:
        summary_text = rolling_payload.get("rolling_summary_text")
        if not isinstance(summary_text, str):
            return validate_rolling_content("")
        return validate_rolling_content(summary_text)

    @classmethod
    def _normalize_rolling_summary_text(cls, rolling_payload: dict) -> str | None:
        validation = cls._validate_and_normalize_rolling_summary_text(rolling_payload)
        if not validation.ok:
            return None
        return validation.normalized_text

    async def fetch_daily_summary(self, *, lead_id: str, memory_day_key: str) -> Optional[str]:
        existing_payload = await self.leads_repo.fetch_daily_summary(
            lead_id=lead_id,
            memory_day_key=memory_day_key,
        )
        if not existing_payload:
            return None
        candidate = existing_payload.get("summary_text")
        return candidate if isinstance(candidate, str) else None

    async def acquire_memory_write_guard(self, *, lead_id: str, idempotency_key: str, created_at: datetime) -> bool:
        return await self.leads_repo.acquire_memory_write_guard(
            lead_id=lead_id,
            idempotency_key=idempotency_key,
            created_at=created_at,
        )

    async def release_memory_write_guard(self, *, lead_id: str, idempotency_key: str) -> None:
        await self.leads_repo.release_memory_write_guard(
            lead_id=lead_id,
            idempotency_key=idempotency_key,
        )

    async def fetch_messages(
        self,
        *,
        lead_id: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[dict]:
        return await fetch_messages_for_window(
            leads_repo=self.leads_repo,
            lead_id=lead_id,
            start_utc=start_utc,
            end_utc=end_utc,
            limit=DAILY_SUMMARY_MESSAGE_LIMIT,
        )

    def build_daily_summary_payload(
        self,
        *,
        memory_day_key: str,
        daily_summary_payload: dict | None,
        messages: list[dict],
        start_utc: datetime,
        end_utc: datetime,
    ) -> DailySummaryWritePayload:
        payload = daily_summary_payload if isinstance(daily_summary_payload, dict) else {}
        return DailySummaryWritePayload(
            memory_day_key=memory_day_key,
            summary_text=str(payload.get("summary_text") or ""),
            open_questions=list(payload.get("open_questions") or []),
            carry_forward_notes=list(payload.get("carry_forward_notes") or []),
            learned_facts=list(payload.get("learned_facts") or []),
            changed_facts=list(payload.get("changed_facts") or []),
            memory_relevance_flags=list(payload.get("memory_relevance_flags") or []),
            created_at=datetime.now(tz=timezone.utc),
            messages_used_count=len(messages),
            source_window_start=start_utc,
            source_window_end=end_utc,
        )

    async def write_daily_summary(self, *, lead_id: str, payload: DailySummaryWritePayload) -> bool:
        return await self.leads_repo.write_daily_summary(
            lead_id=lead_id,
            memory_day_key=payload.memory_day_key,
            summary_text=payload.summary_text,
            open_questions=payload.open_questions,
            carry_forward_notes=payload.carry_forward_notes,
            learned_facts=payload.learned_facts,
            changed_facts=payload.changed_facts,
            memory_relevance_flags=payload.memory_relevance_flags,
            created_at=payload.created_at,
            messages_used_count=payload.messages_used_count,
            source_window_start=payload.source_window_start,
            source_window_end=payload.source_window_end,
        )

    async def update_rolling_summary(self, *, lead_id: str, rolling_update: dict[str, object]) -> bool:
        return await self.leads_repo.update_rolling_summary(
            lead_id=lead_id,
            rolling_update=rolling_update,
            updated_at=datetime.now(tz=timezone.utc),
        )

    async def fetch_confirmed_rolling_summary_text(self, *, lead_id: str) -> str | None:
        rolling_payload = await self.leads_repo.fetch_rolling_summary(lead_id=lead_id)
        if not isinstance(rolling_payload, dict):
            return None
        return self._normalize_rolling_summary_text(rolling_payload)

    async def fetch_confirmed_rolling_summary_validation(
        self,
        *,
        lead_id: str,
        expected_rolling_version: int | None = None,
        expected_rolling_hash: str | None = None,
    ) -> ConfirmedRollingSummaryValidation:
        rolling_payload = await self.leads_repo.fetch_rolling_summary(lead_id=lead_id)
        if not isinstance(rolling_payload, dict):
            return ConfirmedRollingSummaryValidation(
                ok=False,
                reason_code="rolling_payload_missing",
                normalized_text=None,
                rolling_version=None,
                rolling_hash=None,
            )

        content_validation = self._validate_and_normalize_rolling_summary_text(rolling_payload)
        if not content_validation.ok:
            return ConfirmedRollingSummaryValidation(
                ok=False,
                reason_code=content_validation.reason_code,
                normalized_text=content_validation.normalized_text or None,
                rolling_version=None,
                rolling_hash=None,
            )

        rolling_version = rolling_payload.get("version")
        if not isinstance(rolling_version, int) or rolling_version < 1:
            return ConfirmedRollingSummaryValidation(
                ok=False,
                reason_code="rolling_version_missing_or_invalid",
                normalized_text=content_validation.normalized_text,
                rolling_version=None,
                rolling_hash=None,
            )

        rolling_hash_raw = rolling_payload.get("rolling_hash")
        rolling_hash = str(rolling_hash_raw).strip() if isinstance(rolling_hash_raw, str) else ""
        if not rolling_hash:
            return ConfirmedRollingSummaryValidation(
                ok=False,
                reason_code="rolling_hash_missing_or_invalid",
                normalized_text=content_validation.normalized_text,
                rolling_version=rolling_version,
                rolling_hash=None,
            )

        if expected_rolling_version is not None and rolling_version != expected_rolling_version:
            return ConfirmedRollingSummaryValidation(
                ok=False,
                reason_code="rolling_post_commit_version_mismatch",
                normalized_text=content_validation.normalized_text,
                rolling_version=rolling_version,
                rolling_hash=rolling_hash,
            )

        expected_hash_normalized = str(expected_rolling_hash or "").strip() or None
        if expected_hash_normalized is not None and rolling_hash != expected_hash_normalized:
            return ConfirmedRollingSummaryValidation(
                ok=False,
                reason_code="rolling_post_commit_hash_mismatch",
                normalized_text=content_validation.normalized_text,
                rolling_version=rolling_version,
                rolling_hash=rolling_hash,
            )

        return ConfirmedRollingSummaryValidation(
            ok=True,
            reason_code=None,
            normalized_text=content_validation.normalized_text,
            rolling_version=rolling_version,
            rolling_hash=rolling_hash,
        )

    async def apply_memory_agent_updates(
        self,
        *,
        lead,
        active_window_update: dict | None,
        conversation_state_update: dict | None,
        updated_at: datetime,
    ) -> None:
        if self.memory_layer_service is None or lead is None:
            return
        await self.memory_layer_service.apply_active_window_update(
            lead=lead,
            update=active_window_update,
            updated_at=updated_at,
        )
        await self.memory_layer_service.apply_conversation_state_update(
            lead_id=str(getattr(lead, "lead_id", "") or ""),
            update=conversation_state_update,
            updated_at=updated_at,
        )

    async def apply_conversation_state_update(
        self,
        *,
        lead_id: str,
        conversation_state_update: dict | None,
        updated_at: datetime,
    ) -> None:
        if self.memory_layer_service is None:
            return
        await self.memory_layer_service.apply_conversation_state_update(
            lead_id=lead_id,
            update=conversation_state_update,
            updated_at=updated_at,
        )

    async def get_conversation_state_snapshot(self, *, lead_id: str) -> dict | None:
        if self.memory_layer_service is None:
            return None
        state = await self.memory_layer_service.get_conversation_state(lead_id=lead_id)
        return state.model_dump(mode="python", exclude_none=True) if state is not None else None

    async def restore_conversation_state_snapshot(
        self,
        *,
        lead_id: str,
        snapshot: dict | None,
    ) -> None:
        if self.memory_layer_service is None:
            return
        if snapshot is None:
            await self.memory_layer_service.delete_conversation_state(lead_id=lead_id)
            return
        restored = ConversationStateRecord(**snapshot)
        await self.memory_layer_service.upsert_conversation_state(state=restored)
    @staticmethod
    def _daily_payload_matches_existing(*, existing_payload: dict, daily_payload: DailySummaryWritePayload) -> bool:
        comparable_fields = (
            "summary_text",
            "open_questions",
            "carry_forward_notes",
            "learned_facts",
            "changed_facts",
            "memory_relevance_flags",
        )
        incoming = {
            "summary_text": daily_payload.summary_text,
            "open_questions": daily_payload.open_questions,
            "carry_forward_notes": daily_payload.carry_forward_notes,
            "learned_facts": daily_payload.learned_facts,
            "changed_facts": daily_payload.changed_facts,
            "memory_relevance_flags": daily_payload.memory_relevance_flags,
        }
        return all(existing_payload.get(field) == incoming.get(field) for field in comparable_fields)
