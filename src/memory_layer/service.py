from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.settings import load_settings
from src.domain.contracts.persistence import LeadMessageRecord, LeadRepositoryPort
from .domain import MemoryDayBoundaryPolicy, WindowClosePolicy, WindowCloseTiming
from .contracts import MemoryLayerPort
from .models import (
    ActiveWindowRecord,
    ConversationStateRecord,
    MemoryMessageRecord,
    MemoryReadBundle,
)

logger = logging.getLogger(__name__)


class MemoryLayerService:
    """Separate Step 2 memory-layer boundary for operational state updates."""

    _WINDOW_GRACE_PERIOD = timedelta(minutes=1)
    _DAY_CLOSE_HOUR = 20
    _DAY_CLOSE_MINUTE = 5

    def __init__(self, *, repository: MemoryLayerPort, settings=None) -> None:
        self._repository = repository
        self._settings = settings or load_settings()
        self._memory_day_boundary_policy = MemoryDayBoundaryPolicy()

    async def build_read_bundle(
        self,
        *,
        lead_id: str,
        lead,
        leads_repo: LeadRepositoryPort,
        since: datetime,
        last_messages_limit: int,
    ) -> MemoryReadBundle:
        active_window = await self._repository.get_active_window(lead_id=lead_id)
        conversation_state = await self._repository.get_conversation_state(lead_id=lead_id)
        rolling_summary = self._extract_lead_rolling_summary(lead)
        try:
            rolling_summary_doc = await leads_repo.fetch_rolling_summary(lead_id=str(lead_id))
            if isinstance(rolling_summary_doc, dict):
                rolling_summary = self._extract_rolling_summary_text(rolling_summary_doc)
            else:
                rolling_summary = None
        except Exception:
            logger.warning("memory_layer_rolling_summary_failed", extra={"lead_id": lead_id}, exc_info=True)

        messages: list[MemoryMessageRecord] = []
        try:
            messages_raw = await leads_repo.fetch_last_messages(
                lead_id=str(lead_id),
                since=since,
                limit=last_messages_limit,
            )
        except Exception:
            logger.warning("memory_layer_messages_failed", extra={"lead_id": lead_id}, exc_info=True)
            messages_raw = []

        for entry in messages_raw:
            mapped = self._to_memory_message(entry)
            if mapped is None:
                continue
            messages.append(mapped)
        messages.sort(key=lambda item: item.ts or "")

        daily_summary = None
        try:
            daily_summary_doc = await leads_repo.fetch_latest_daily_summary(lead_id=str(lead_id))
            if daily_summary_doc:
                daily_summary = daily_summary_doc.get("summary_text")
        except Exception:
            logger.warning("memory_layer_daily_summary_failed", extra={"lead_id": lead_id}, exc_info=True)

        return MemoryReadBundle(
            rolling_summary=rolling_summary,
            daily_summary=daily_summary,
            messages=messages,
            active_window=active_window,
            conversation_state=conversation_state,
        )

    @staticmethod
    def _extract_lead_rolling_summary(lead) -> str | None:
        candidate = getattr(lead, "rolling_summary", None)
        if isinstance(candidate, str):
            normalized = candidate.strip()
            return normalized or None
        return None

    @staticmethod
    def _extract_rolling_summary_text(payload: object) -> str | None:
        if not isinstance(payload, dict):
            return None
        candidate = payload.get("rolling_summary_text")
        if not isinstance(candidate, str):
            return None
        normalized = candidate.strip()
        return normalized or None

    def _to_memory_message(self, payload: LeadMessageRecord) -> MemoryMessageRecord | None:
        role = payload.get("role")
        text = payload.get("text")
        ts_value = payload.get("timestamp")
        if not isinstance(role, str) or not role.strip():
            return None
        if not isinstance(text, str) or not text.strip():
            return None
        ts = ts_value if isinstance(ts_value, datetime) else None
        return MemoryMessageRecord(
            role=role.strip(),
            text=text,
            ts=self._safe_isoformat(ts),
        )

    async def list_active_windows(
        self,
        *,
        statuses: list[str] | None = None,
    ) -> list[ActiveWindowRecord]:
        return await self._repository.list_active_windows(statuses=statuses)

    async def get_active_window(self, *, lead_id: str) -> ActiveWindowRecord | None:
        return await self._repository.get_active_window(lead_id=lead_id)

    async def get_conversation_state(self, *, lead_id: str) -> ConversationStateRecord | None:
        return await self._repository.get_conversation_state(lead_id=lead_id)

    async def delete_conversation_state(self, *, lead_id: str) -> None:
        await self._repository.delete_conversation_state(lead_id=lead_id)

    async def upsert_conversation_state(self, *, state: ConversationStateRecord) -> ConversationStateRecord:
        return await self._repository.upsert_conversation_state(state=state)

    async def observe_turn(
        self,
        *,
        lead,
        session,
        user_text: str,
        reply_text: str,
        occurred_at: datetime,
        user_message_id: str | None = None,
        assistant_message_id: str | None = None,
    ) -> None:
        lead_id = str(getattr(lead, "lead_id", "") or "").strip()
        if not lead_id:
            return

        timezone_name = self._resolve_timezone_name(lead)
        local_day_key = self._compute_local_day_key(occurred_at=occurred_at, timezone_name=timezone_name)
        user_message_id = self._normalize_message_id(user_message_id)
        assistant_message_id = self._normalize_message_id(assistant_message_id)

        window = await self._repository.get_active_window(lead_id=lead_id)
        if window is None or window.local_day_key != local_day_key:
            window = ActiveWindowRecord(
                lead_id=lead_id,
                timezone=timezone_name,
                local_day_key=local_day_key,
                window_status="open",
                opened_at=occurred_at,
                last_activity_at=occurred_at,
                grace_until=self._resolve_window_close_timing(
                    opened_at=occurred_at,
                    last_activity_at=occurred_at,
                    timezone_name=timezone_name,
                ).grace_until_utc,
                first_message_id=user_message_id or assistant_message_id,
                last_message_id=assistant_message_id or user_message_id,
                last_assistant_message_id=assistant_message_id,
                message_count=0,
                updated_at=occurred_at,
            )

        message_delta = int(bool(user_text)) + int(bool(reply_text))
        updated_window = window.model_copy(
            update={
                "timezone": timezone_name,
                "window_status": "open",
                "last_activity_at": occurred_at,
                "grace_until": self._resolve_window_close_timing(
                    opened_at=window.opened_at,
                    last_activity_at=occurred_at,
                    timezone_name=timezone_name,
                ).grace_until_utc,
                "last_user_message_at": occurred_at if user_text else window.last_user_message_at,
                "last_assistant_message_at": occurred_at if reply_text else window.last_assistant_message_at,
                "first_message_id": window.first_message_id or user_message_id or assistant_message_id,
                "last_message_id": assistant_message_id or user_message_id or window.last_message_id,
                "last_assistant_message_id": assistant_message_id or window.last_assistant_message_id,
                "message_count": window.message_count + message_delta,
                "updated_at": occurred_at,
            }
        )
        await self._repository.upsert_active_window(window=updated_window)

        previous_state = await self._repository.get_conversation_state(lead_id=lead_id)
        current_stage = getattr(lead, "stage", None) or getattr(session, "current_stage", None)
        current_version = previous_state.state_version if previous_state is not None else 0
        conversation_state = ConversationStateRecord(
            lead_id=lead_id,
            current_stage=current_stage,
            pending_question=previous_state.pending_question if previous_state else None,
            open_questions=list(previous_state.open_questions) if previous_state else [],
            answered_topics=list(previous_state.answered_topics) if previous_state else [],
            followup_status=previous_state.followup_status if previous_state else None,
            last_agent_role="assistant" if reply_text else (previous_state.last_agent_role if previous_state else None),
            response_mode=previous_state.response_mode if previous_state else None,
            next_expected_move=previous_state.next_expected_move if previous_state else None,
            state_version=current_version + 1,
            updated_at=occurred_at,
        )
        await self._repository.upsert_conversation_state(state=conversation_state)

    async def sync_active_window_timezone(
        self,
        *,
        lead_id: str,
        timezone_name: str,
        updated_at: datetime | None = None,
    ) -> ActiveWindowRecord | None:
        normalized_lead_id = str(lead_id or "").strip()
        normalized_timezone = self._normalize_timezone_name(timezone_name)
        if not normalized_lead_id or not normalized_timezone:
            logger.info(
                "active_window_timezone_sync_skipped",
                extra={"lead_id": normalized_lead_id or None, "reason": "lead_timezone_not_updated"},
            )
            return None

        window = await self._repository.get_active_window(lead_id=normalized_lead_id)
        if window is None:
            logger.info(
                "active_window_timezone_sync_skipped",
                extra={"lead_id": normalized_lead_id, "reason": "no_open_window"},
            )
            return None
        if window.timezone == normalized_timezone:
            logger.info(
                "active_window_timezone_sync_skipped",
                extra={"lead_id": normalized_lead_id, "reason": "window_already_in_sync"},
            )
            return window

        logger.info(
            "active_window_timezone_sync_started",
            extra={
                "lead_id": normalized_lead_id,
                "from_timezone": window.timezone,
                "to_timezone": normalized_timezone,
            },
        )

        persisted_at = updated_at or datetime.now(tz=timezone.utc)
        updated_window = window.model_copy(
            update={
                "timezone": normalized_timezone,
                "local_day_key": self._compute_local_day_key(
                    occurred_at=window.opened_at,
                    timezone_name=normalized_timezone,
                ),
                "grace_until": self._resolve_window_close_timing(
                    opened_at=window.opened_at,
                    last_activity_at=window.last_activity_at,
                    timezone_name=normalized_timezone,
                ).grace_until_utc,
                "updated_at": persisted_at,
            }
        )
        stored_window = await self._repository.upsert_active_window(window=updated_window)
        logger.info(
            "active_window_timezone_sync_applied",
            extra={"lead_id": normalized_lead_id, "timezone": normalized_timezone},
        )
        return stored_window

    async def refresh_active_window_lifecycle(
        self,
        *,
        lead,
        as_of: datetime,
    ) -> ActiveWindowRecord | None:
        lead_id = str(getattr(lead, "lead_id", "") or "").strip()
        if not lead_id:
            return None

        window = await self._repository.get_active_window(lead_id=lead_id)
        if window is None:
            return None

        timezone_name = self._resolve_timezone_name(lead)
        desired_status, reason_codes, diagnostics = self._resolve_window_status_with_reason(
            window=window,
            timezone_name=timezone_name,
            as_of=as_of,
        )
        logger.debug(
            "active_window_lifecycle_resolved",
            extra={
                "lead_id": lead_id,
                "previous_status": window.window_status,
                "resolved_status": desired_status,
                "reason_codes": reason_codes,
                "window_local_day_key": window.local_day_key,
                "timezone": timezone_name,
                "as_of": as_of.isoformat(),
                **diagnostics,
            },
        )
        if desired_status == window.window_status and window.timezone == timezone_name:
            return window

        updated_window = window.model_copy(
            update={
                "timezone": timezone_name,
                "window_status": desired_status,
                "updated_at": as_of,
            }
        )
        return await self._repository.upsert_active_window(window=updated_window)

    async def close_active_window(
        self,
        *,
        lead,
        closed_at: datetime,
    ) -> ActiveWindowRecord | None:
        lead_id = str(getattr(lead, "lead_id", "") or "").strip()
        if not lead_id:
            return None

        window = await self._repository.get_active_window(lead_id=lead_id)
        if window is None:
            return None

        updated_window = window.model_copy(
            update={
                "timezone": self._resolve_timezone_name(lead),
                "window_status": "closed",
                "updated_at": closed_at,
            }
        )
        return await self._repository.upsert_active_window(window=updated_window)

    async def apply_active_window_update(
        self,
        *,
        lead,
        update: dict[str, object] | None,
        updated_at: datetime,
    ) -> ActiveWindowRecord | None:
        lead_id = str(getattr(lead, "lead_id", "") or "").strip()
        if not lead_id:
            return None

        window = await self._repository.get_active_window(lead_id=lead_id)
        if window is None or not isinstance(update, dict):
            return window

        patch: dict[str, object] = {"updated_at": updated_at}
        if isinstance(update.get("open_topics"), list):
            patch["open_topics"] = [str(item) for item in update.get("open_topics") or [] if str(item).strip()]
        if isinstance(update.get("local_context_text"), str):
            patch["local_context_text"] = str(update.get("local_context_text") or "").strip() or None
        if isinstance(update.get("window_status"), str):
            candidate_status = str(update.get("window_status") or "").strip().lower()
            if candidate_status in {"open", "closing", "closed"}:
                patch["window_status"] = candidate_status

        updated_window = window.model_copy(update=patch)
        return await self._repository.upsert_active_window(window=updated_window)

    async def apply_conversation_state_update(
        self,
        *,
        lead_id: str,
        update: dict[str, object] | None,
        updated_at: datetime,
    ) -> ConversationStateRecord | None:
        normalized_lead_id = str(lead_id or "").strip()
        if not normalized_lead_id:
            return None

        previous_state = await self._repository.get_conversation_state(lead_id=normalized_lead_id)
        if previous_state is None and not isinstance(update, dict):
            return None

        base_state = previous_state or ConversationStateRecord(
            lead_id=normalized_lead_id,
            updated_at=updated_at,
        )
        patch: dict[str, object] = {
            "updated_at": updated_at,
            "state_version": base_state.state_version + 1,
        }
        if isinstance(update, dict):
            for key in (
                "current_stage",
                "pending_question",
                "followup_status",
                "last_agent_role",
                "response_mode",
                "next_expected_move",
            ):
                if key in update:
                    patch[key] = update.get(key)
            for key in ("open_questions", "answered_topics"):
                if isinstance(update.get(key), list):
                    patch[key] = [str(item) for item in update.get(key) or [] if str(item).strip()]

        updated_state = base_state.model_copy(update=patch)
        return await self._repository.upsert_conversation_state(state=updated_state)

    def _resolve_timezone_name(self, lead) -> str:
        raw_timezone = getattr(lead, "timezone", None)
        normalized_timezone = self._normalize_timezone_name(raw_timezone)
        if normalized_timezone:
            return normalized_timezone

        fallback = getattr(self._settings, "memory_summary_timezone", "Asia/Almaty")
        try:
            ZoneInfo(fallback)
            return fallback
        except Exception:
            return "UTC"

    @staticmethod
    def _normalize_timezone_name(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        candidate = value.strip()
        if not candidate:
            return None
        try:
            ZoneInfo(candidate)
        except Exception:
            return None
        return candidate

    def _compute_local_day_key(self, *, occurred_at: datetime, timezone_name: str) -> str:
        boundary = self._resolve_memory_day_boundary(occurred_at=occurred_at, timezone_name=timezone_name)
        return boundary.memory_day_key

    def _resolve_memory_day_boundary(self, *, occurred_at: datetime, timezone_name: str):
        # Memory-day boundaries are domain-owned. Do not reintroduce calendar-day formulas here.
        return self._memory_day_boundary_policy.resolve_for_event(
            occurred_at_utc=occurred_at,
            timezone_name=timezone_name,
            cutoff_hour=self._DAY_CLOSE_HOUR,
            cutoff_minute=self._DAY_CLOSE_MINUTE,
        )

    def resolve_window_close_timing(
        self,
        *,
        opened_at: datetime,
        last_activity_at: datetime,
        timezone_name: str,
    ) -> WindowCloseTiming:
        return self._resolve_window_close_timing(
            opened_at=opened_at,
            last_activity_at=last_activity_at,
            timezone_name=timezone_name,
        )

    def _resolve_window_status(
        self,
        *,
        window: ActiveWindowRecord,
        timezone_name: str,
        as_of: datetime,
    ) -> str:
        status, _, _ = self._resolve_window_status_with_reason(
            window=window,
            timezone_name=timezone_name,
            as_of=as_of,
        )
        return status

    def _resolve_window_status_with_reason(
        self,
        *,
        window: ActiveWindowRecord,
        timezone_name: str,
        as_of: datetime,
    ) -> tuple[str, list[str], dict[str, str | None]]:
        resolved_timezone_name = self._normalize_timezone_name(window.timezone) or timezone_name
        close_timing = self._resolve_window_close_timing(
            opened_at=window.opened_at,
            last_activity_at=window.last_activity_at,
            timezone_name=resolved_timezone_name,
        )
        grace_until = close_timing.grace_until_utc
        window_close_at_utc = close_timing.window_close_at_utc

        diagnostics: dict[str, str | None] = {
            "grace_until": grace_until.isoformat(),
            "time_close_threshold": close_timing.close_threshold_utc.isoformat(),
            "window_close_at_utc": window_close_at_utc.isoformat(),
            "as_of_local": None,
        }
        if window.window_status == "closed":
            return "closed", ["already_closed"], diagnostics

        as_of_local = as_of.astimezone(ZoneInfo(resolved_timezone_name))
        diagnostics["as_of_local"] = as_of_local.isoformat()

        if as_of >= window_close_at_utc:
            return "closing", ["ready_to_close"], diagnostics
        return "open", ["before_cutoff"], diagnostics

    def _resolve_window_close_timing(
        self,
        *,
        opened_at: datetime,
        last_activity_at: datetime,
        timezone_name: str,
    ) -> WindowCloseTiming:
        return WindowClosePolicy.resolve(
            opened_at=opened_at,
            last_activity_at=last_activity_at,
            timezone_name=timezone_name,
            cutoff_hour=self._DAY_CLOSE_HOUR,
            cutoff_minute=self._DAY_CLOSE_MINUTE,
            grace_period=self._WINDOW_GRACE_PERIOD,
        )

    @staticmethod
    def _safe_isoformat(value: datetime | None) -> str | None:
        if not value:
            return None
        return value.astimezone(ZoneInfo("UTC")).isoformat()

    @staticmethod
    def _normalize_message_id(value: object) -> str | None:
        if isinstance(value, str):
            candidate = value.strip()
            return candidate or None
        return None
