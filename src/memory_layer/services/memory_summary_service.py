"""Daily memory summary service used by Cloud Scheduler trigger."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone, timedelta
from typing import Any, Mapping, Optional
from zoneinfo import ZoneInfo

import anyio

from src.memory_layer import FirestoreMemoryLayerRepository, MemoryLayerService
from src.memory_layer.run_ledger_repository import FirestoreMemoryRunLedgerRepository
from src.memory_layer.domain import MemoryDayBoundaryPolicy, MemoryRunResult, WindowClosePolicy
from src.settings import load_settings
from src.utils.log_redaction import redact
from src.adapters.database.firestore.firestore_repositories import FirestoreLeadRepository
from src.memory_layer.use_cases import (
    ApplyDailyAgentOutputUseCase,
    ApplyRollingMemoryAgentOutputUseCase,
    ProcessDailyAgentOutputUseCase,
    ProcessRollingMemoryAgentOutputUseCase,
)
from src.services.crm.crm_memory_sync_service import CrmMemorySyncService
from src.services.runtime.feature_flags import resolve_feature_flags
from .memory_run_ledger_service import MemoryRunLedgerService
from .memory_lead_selector import MemoryLeadSelector
from .memory_sync_port import MemorySyncPort
from .memory_sync_llm_service import MemorySummaryService as MemorySyncLLMService
from .memory_sync_persistence_service import MemorySyncPersistenceService

logger = logging.getLogger(__name__)


@dataclass
class MemorySummaryResult:
    """Result of the daily memory summary job.

    `errors` is an internal diagnostics channel for logs/service consumers.
    API handlers must expose only aggregate counters and coarse statuses.
    """

    date: date
    leads_processed: int = 0
    summaries_written: int = 0
    errors: list[str] = field(default_factory=list)
    failed_leads: list[dict[str, str]] = field(default_factory=list)
    total_selected: int = 0
    updated: bool = False
    rows_written: int = 0
    outcome_counts: dict[str, int] = field(
        default_factory=lambda: {
            "success": 0,
            "rejected": 0,
            "skipped": 0,
            "idempotent_noop": 0,
            "failed": 0,
        }
    )
    reason_code_counts: dict[str, int] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        """Aggregate failures count safe for external responses."""
        return len(self.errors)

    @property
    def total_processed(self) -> int:
        return self.leads_processed

    @property
    def total_succeeded(self) -> int:
        return self.outcome_counts.get("success", 0)

    @property
    def total_failed(self) -> int:
        return self.outcome_counts.get("failed", 0)


@dataclass(frozen=True)
class LeadDailySummaryWindow:
    """Per-lead local-day window used by Step 2 memory summarization."""

    memory_day_key: str
    timezone_name: str
    start_utc: datetime
    end_utc: datetime


class MemorySummaryService:
    """Aggregates daily user activity summaries for internal use."""

    def __init__(
        self,
        firestore,
        settings=None,
        leads_repo: Optional[FirestoreLeadRepository] = None,
        memory_layer_service: MemoryLayerService | None = None,
        memory_run_ledger_service: MemoryRunLedgerService | None = None,
    ) -> None:
        self.firestore = firestore
        self.settings = settings or load_settings()
        self.leads_repo = leads_repo or FirestoreLeadRepository()
        self.lead_selector = MemoryLeadSelector(firestore=self.firestore)
        self.memory_layer_service = memory_layer_service or MemoryLayerService(
            repository=FirestoreMemoryLayerRepository(),
            settings=self.settings,
        )
        feature_flags = resolve_feature_flags(self.settings)
        persistence_service = MemorySyncPersistenceService(
            leads_repo=self.leads_repo,
            memory_layer_service=self.memory_layer_service,
        )
        ledger_service = memory_run_ledger_service or MemoryRunLedgerService(
            repository=FirestoreMemoryRunLedgerRepository()
        )
        self.sync_port = MemorySyncPort(
            leads_repo=self.leads_repo,
            memory_summary_service=MemorySyncLLMService(settings=self.settings),
            persistence_service=persistence_service,
            crm_memory_sync_service=CrmMemorySyncService(leads_repo=self.leads_repo),
            process_daily_agent_output_use_case=ProcessDailyAgentOutputUseCase(feature_flags=feature_flags),
            apply_daily_agent_output_use_case=ApplyDailyAgentOutputUseCase(
                persistence_service=persistence_service,
            ),
            process_rolling_agent_output_use_case=ProcessRollingMemoryAgentOutputUseCase(),
            apply_rolling_agent_output_use_case=ApplyRollingMemoryAgentOutputUseCase(
                persistence_service=persistence_service,
            ),
            memory_run_ledger_service=ledger_service,
            feature_flags=feature_flags,
        )

    async def build_memory_summary_for_lead(self, lead_id: str | None = None) -> MemorySummaryResult:
        """Lightweight summary updater used by the Cloud Tasks endpoint."""
        return await self.run_daily_summary_job(lead_id=lead_id)

    async def run_daily_summary_job(
        self,
        *,
        lead_id: Optional[str] = None,
        target_date: Optional[date] = None,
    ) -> MemorySummaryResult:
        if not getattr(self.settings, "memory_summary_enabled", True):
            logger.info("Memory summary is disabled in settings")
            return MemorySummaryResult(date=target_date or date.today())

        if not self.firestore:
            logger.warning("Memory summary skipped: Firestore unavailable")
            return MemorySummaryResult(date=target_date or date.today())

        if target_date is None:
            return await self._run_active_window_summary_job(lead_id=lead_id)

        default_tz = self._timezone()
        default_date_to_process = target_date or self._yesterday(default_tz)

        logger.info(
            "daily_summary_job_started",
            extra={
                "date": default_date_to_process.isoformat(),
                "lead_id": lead_id,
                "default_timezone": getattr(default_tz, "key", str(default_tz)),
            },
        )

        result = MemorySummaryResult(date=default_date_to_process)

        if lead_id:
            leads = [{"lead_id": lead_id}]
        else:
            selection_start_utc, selection_end_utc = self._batch_candidate_window(
                target_date=default_date_to_process,
                tz=default_tz,
            )
            try:
                leads = await anyio.to_thread.run_sync(
                    self.lead_selector.fetch_active_leads,
                    selection_start_utc,
                    selection_end_utc,
                    abandon_on_cancel=True,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Failed to fetch leads for daily summary: %s", redact(exc))
                result.errors.append(redact(exc))
                return result

        for lead in leads:
            resolved_lead_id = lead.get("lead_id") or lead.get("id")
            if not resolved_lead_id:
                continue
            try:
                lead_window = await self._resolve_lead_daily_summary_window(
                    lead_id=str(resolved_lead_id),
                    target_date=target_date,
                    lead_hint=lead,
                )
                updated = await self.sync_port.process_lead_daily_summary(
                    lead_id=str(resolved_lead_id),
                    start_utc=lead_window.start_utc,
                    end_utc=lead_window.end_utc,
                    memory_day_key=lead_window.memory_day_key,
                    errors=result.errors,
                )
                result.leads_processed += 1
                self._record_run_outcome(result=result, lead_id=str(resolved_lead_id), run_result=updated)
                if updated.outcome == "success":
                    result.summaries_written += 1
                    result.updated = True
                    result.rows_written += 1
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Daily summary failed for %s: %s", resolved_lead_id, redact(exc))
                result.errors.append(redact(exc))

        return result

    async def _run_active_window_summary_job(
        self,
        *,
        lead_id: Optional[str] = None,
    ) -> MemorySummaryResult:
        as_of = datetime.now(tz=timezone.utc)
        result = MemorySummaryResult(date=as_of.date())
        batch_mode = not lead_id
        if batch_mode:
            logger.info("memory_summary_batch_started", extra={"as_of": as_of.isoformat()})
        candidates = await self._collect_closing_windows(lead_id=lead_id, as_of=as_of)
        if batch_mode:
            configured_limit = max(1, int(getattr(self.settings, "memory_summary_batch_limit", 100)))
            result.total_selected = len(candidates)
            deferred_count = max(0, len(candidates) - configured_limit)
            if deferred_count > 0:
                logger.info(
                    "memory_summary_batch_selected",
                    extra={
                        "total_selected": len(candidates),
                        "batch_limit": configured_limit,
                        "total_scheduled": configured_limit,
                        "total_deferred": deferred_count,
                    },
                )
            else:
                logger.info(
                    "memory_summary_batch_selected",
                    extra={
                        "total_selected": len(candidates),
                        "batch_limit": configured_limit,
                        "total_scheduled": len(candidates),
                        "total_deferred": 0,
                    },
                )
            candidates = candidates[:configured_limit]
        else:
            result.total_selected = len(candidates)

        for lead, window in candidates:
            try:
                if batch_mode:
                    logger.info(
                        "memory_summary_batch_lead_started",
                        extra={"lead_id": str(window.lead_id), "memory_day_key": window.local_day_key},
                    )
                updated = await self.sync_port.process_lead_daily_summary(
                    lead_id=str(window.lead_id),
                    start_utc=window.opened_at,
                    end_utc=self._resolve_window_close_at_utc(window=window),
                    memory_day_key=window.local_day_key,
                    errors=result.errors,
                )
                result.leads_processed += 1
                self._record_run_outcome(result=result, lead_id=str(window.lead_id), run_result=updated)
                terminal_for_window_close = updated.outcome in {"success", "rejected", "skipped", "idempotent_noop"} and (
                    updated.conflict_class in {None, "duplicate_complete"}
                )
                if terminal_for_window_close:
                    await self.memory_layer_service.close_active_window(lead=lead, closed_at=as_of)
                if updated.outcome == "success":
                    if batch_mode:
                        logger.info(
                            "memory_summary_batch_lead_succeeded",
                            extra={"lead_id": str(window.lead_id), "updated": True},
                        )
                    logger.info(
                        "closing_window_summary_resolved",
                        extra=self._window_trace_extra(
                            lead_id=str(window.lead_id),
                            previous_window=window,
                            refreshed_window=window,
                            as_of=as_of,
                            resolved_status="closed",
                            reason_codes=["summary_written", "window_closed"],
                        ),
                    )
                    result.summaries_written += 1
                    result.updated = True
                    result.rows_written += 1
                    continue
                if updated.outcome == "failed":
                    failure_reason = updated.reason_code or "summary_error"
                    if batch_mode:
                        logger.error(
                            "memory_summary_batch_lead_failed",
                            extra={"lead_id": str(window.lead_id), "reason": failure_reason},
                        )
                    logger.error(
                        "closing_window_summary_failed_retry_pending",
                        extra=self._window_trace_extra(
                            lead_id=str(window.lead_id),
                            previous_window=window,
                            refreshed_window=window,
                            as_of=as_of,
                            resolved_status="closing",
                            reason_codes=["summary_error", "retry_pending"],
                        ),
                    )
                    continue
                logger.info(
                    "closing_window_summary_not_updated_window_closed",
                    extra=self._window_trace_extra(
                        lead_id=str(window.lead_id),
                        previous_window=window,
                        refreshed_window=window,
                        as_of=as_of,
                        resolved_status="closed",
                            reason_codes=["summary_not_updated", "window_closed"],
                        ),
                    )
                if batch_mode:
                    logger.info(
                        "memory_summary_batch_lead_succeeded",
                        extra={"lead_id": str(window.lead_id), "updated": False},
                    )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Closing window summary failed for %s: %s", window.lead_id, redact(exc))
                result.errors.append(redact(exc))
                failure_reason = str(redact(exc))[:256]
                result.failed_leads.append({"lead_id": str(window.lead_id), "reason": failure_reason})
                if batch_mode:
                    logger.error(
                        "memory_summary_batch_lead_failed",
                        extra={"lead_id": str(window.lead_id), "reason": failure_reason},
                    )
                logger.error(
                    "closing_window_summary_exception_retry_pending",
                    extra=self._window_trace_extra(
                        lead_id=str(window.lead_id),
                        previous_window=window,
                        refreshed_window=window,
                        as_of=as_of,
                        resolved_status="closing",
                        reason_codes=["summary_exception", "retry_pending"],
                    ),
                )

        if batch_mode:
            logger.info(
                "memory_summary_batch_finished",
                extra={
                    "total_selected": result.total_selected,
                    "total_processed": result.total_processed,
                    "total_succeeded": result.total_succeeded,
                    "total_failed": result.total_failed,
                },
            )
        return result

    @staticmethod
    def _record_run_outcome(
        *,
        result: MemorySummaryResult,
        lead_id: str,
        run_result: MemoryRunResult,
    ) -> None:
        result.outcome_counts[run_result.outcome] = result.outcome_counts.get(run_result.outcome, 0) + 1
        if run_result.reason_code:
            result.reason_code_counts[run_result.reason_code] = result.reason_code_counts.get(run_result.reason_code, 0) + 1
        if run_result.outcome == "failed":
            result.errors.append(run_result.reason_code or "memory_run_failed")
            result.failed_leads.append({"lead_id": lead_id, "reason": run_result.reason_code or "memory_run_failed"})

    async def _collect_closing_windows(
        self,
        *,
        lead_id: Optional[str],
        as_of: datetime,
    ) -> list[tuple[object, Any]]:
        if lead_id:
            previous_window = await self.memory_layer_service.get_active_window(lead_id=str(lead_id))
            lead = await self.leads_repo.get(str(lead_id))
            if not lead:
                self._log_window_exclusion(
                    lead_id=str(lead_id),
                    previous_window=previous_window,
                    refreshed_window=None,
                    as_of=as_of,
                    exclusion_reason="lead_missing",
                )
                return []
            refreshed = await self.memory_layer_service.refresh_active_window_lifecycle(
                lead=lead,
                as_of=as_of,
            )
            self._log_window_refresh_evaluation(
                lead_id=str(lead_id),
                previous_window=previous_window,
                refreshed_window=refreshed,
                as_of=as_of,
            )
            if refreshed is None or refreshed.window_status != "closing":
                self._log_window_exclusion(
                    lead_id=str(lead_id),
                    previous_window=previous_window,
                    refreshed_window=refreshed,
                    as_of=as_of,
                    exclusion_reason="window_missing" if refreshed is None else "not_closing_after_refresh",
                )
                return []
            return [(lead, refreshed)]

        windows = await self.memory_layer_service.list_active_windows(statuses=["open", "closing"])
        candidates: list[tuple[object, Any]] = []
        for window in windows:
            lead = await self.leads_repo.get(str(window.lead_id))
            if not lead:
                self._log_window_exclusion(
                    lead_id=str(window.lead_id),
                    previous_window=window,
                    refreshed_window=None,
                    as_of=as_of,
                    exclusion_reason="lead_missing",
                )
                continue
            refreshed = await self.memory_layer_service.refresh_active_window_lifecycle(
                lead=lead,
                as_of=as_of,
            )
            self._log_window_refresh_evaluation(
                lead_id=str(window.lead_id),
                previous_window=window,
                refreshed_window=refreshed,
                as_of=as_of,
            )
            if refreshed is None or refreshed.window_status != "closing":
                self._log_window_exclusion(
                    lead_id=str(window.lead_id),
                    previous_window=window,
                    refreshed_window=refreshed,
                    as_of=as_of,
                    exclusion_reason="window_missing" if refreshed is None else "not_closing_after_refresh",
                )
                continue
            candidates.append((lead, refreshed))
        return candidates

    def _log_window_refresh_evaluation(
        self,
        *,
        lead_id: str,
        previous_window: Any | None,
        refreshed_window: Any | None,
        as_of: datetime,
    ) -> None:
        logger.debug(
            "closing_window_refresh_evaluated",
            extra=self._window_trace_extra(
                lead_id=lead_id,
                previous_window=previous_window,
                refreshed_window=refreshed_window,
                as_of=as_of,
                resolved_status=getattr(refreshed_window, "window_status", None),
                reason_codes=["lifecycle_refreshed"],
            ),
        )

    def _log_window_exclusion(
        self,
        *,
        lead_id: str,
        previous_window: Any | None,
        refreshed_window: Any | None,
        as_of: datetime,
        exclusion_reason: str,
    ) -> None:
        logger.debug(
            "closing_window_excluded",
            extra=self._window_trace_extra(
                lead_id=lead_id,
                previous_window=previous_window,
                refreshed_window=refreshed_window,
                as_of=as_of,
                resolved_status=getattr(refreshed_window, "window_status", None)
                or getattr(previous_window, "window_status", None),
                reason_codes=[exclusion_reason],
            ),
        )

    @staticmethod
    def _window_trace_extra(
        *,
        lead_id: str,
        previous_window: Any | None,
        refreshed_window: Any | None,
        as_of: datetime,
        resolved_status: str | None,
        reason_codes: list[str],
    ) -> dict[str, Any]:
        timezone_name = (
            getattr(refreshed_window, "timezone", None)
            or getattr(previous_window, "timezone", None)
            or "UTC"
        )
        source_window = refreshed_window or previous_window
        close_timing = None
        if source_window is not None:
            close_timing = WindowClosePolicy.resolve(
                opened_at=getattr(source_window, "opened_at"),
                last_activity_at=getattr(source_window, "last_activity_at"),
                timezone_name=timezone_name,
                cutoff_hour=MemoryLayerService._DAY_CLOSE_HOUR,
                cutoff_minute=MemoryLayerService._DAY_CLOSE_MINUTE,
                grace_period=MemoryLayerService._WINDOW_GRACE_PERIOD,
            )
        return {
            "lead_id": lead_id,
            "previous_status": getattr(previous_window, "window_status", None),
            "refreshed_status": getattr(refreshed_window, "window_status", None),
            "local_day_key": getattr(refreshed_window, "local_day_key", None)
            or getattr(previous_window, "local_day_key", None),
            "timezone": timezone_name,
            "grace_until": close_timing.grace_until_utc.isoformat() if close_timing else None,
            "close_threshold": close_timing.close_threshold_utc.isoformat() if close_timing else None,
            "window_close_at_utc": close_timing.window_close_at_utc.isoformat() if close_timing else None,
            "as_of": as_of.isoformat(),
            "resolved_status": resolved_status,
            "reason_codes": reason_codes,
        }

    @staticmethod
    def _resolve_window_close_at_utc(*, window: Any) -> datetime:
        close_timing = WindowClosePolicy.resolve(
            opened_at=window.opened_at,
            last_activity_at=window.last_activity_at,
            timezone_name=window.timezone,
            cutoff_hour=MemoryLayerService._DAY_CLOSE_HOUR,
            cutoff_minute=MemoryLayerService._DAY_CLOSE_MINUTE,
            grace_period=MemoryLayerService._WINDOW_GRACE_PERIOD,
        )
        return close_timing.window_close_at_utc

    def _timezone(self) -> ZoneInfo:
        tz_name = getattr(self.settings, "memory_summary_timezone", "Asia/Almaty")
        return self._safe_timezone(tz_name)

    @staticmethod
    def _safe_timezone(tz_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(tz_name)
        except Exception:  # pragma: no cover - system configuration
            logger.warning("Unknown timezone %s, falling back to UTC", tz_name)
            return ZoneInfo("UTC")

    @staticmethod
    def _extract_timezone_name(lead_hint: Mapping[str, Any] | object | None) -> Optional[str]:
        if lead_hint is None:
            return None
        if isinstance(lead_hint, Mapping):
            raw = lead_hint.get("timezone")
        else:
            raw = getattr(lead_hint, "timezone", None)
        if not isinstance(raw, str):
            return None
        candidate = raw.strip()
        return candidate or None

    async def _resolve_lead_daily_summary_window(
        self,
        *,
        lead_id: str,
        target_date: Optional[date],
        lead_hint: Mapping[str, Any] | object | None = None,
    ) -> LeadDailySummaryWindow:
        timezone_name = self._extract_timezone_name(lead_hint)
        if not timezone_name:
            lead = await self.leads_repo.get(lead_id)
            timezone_name = self._extract_timezone_name(lead)

        effective_tz = self._safe_timezone(timezone_name or getattr(self.settings, "memory_summary_timezone", "Asia/Almaty"))
        effective_date = target_date or self._yesterday(effective_tz)
        boundary = MemoryDayBoundaryPolicy.resolve_for_memory_day_key(
            memory_day_key=effective_date.isoformat(),
            timezone_name=getattr(effective_tz, "key", str(effective_tz)),
            cutoff_hour=MemoryLayerService._DAY_CLOSE_HOUR,
            cutoff_minute=MemoryLayerService._DAY_CLOSE_MINUTE,
        )
        return LeadDailySummaryWindow(
            memory_day_key=boundary.memory_day_key,
            timezone_name=getattr(effective_tz, "key", str(effective_tz)),
            start_utc=boundary.memory_day_start_utc,
            end_utc=boundary.memory_day_end_utc,
        )

    @staticmethod
    def _batch_candidate_window(*, target_date: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
        boundary = MemoryDayBoundaryPolicy.resolve_for_memory_day_key(
            memory_day_key=target_date.isoformat(),
            timezone_name=getattr(tz, "key", str(tz)),
            cutoff_hour=MemoryLayerService._DAY_CLOSE_HOUR,
            cutoff_minute=MemoryLayerService._DAY_CLOSE_MINUTE,
        )
        expanded_start = boundary.memory_day_start_utc - timedelta(days=1)
        expanded_end = boundary.memory_day_end_utc + timedelta(days=1)
        return expanded_start, expanded_end

    @staticmethod
    def _yesterday(tz: ZoneInfo) -> date:
        now_local = datetime.now(tz=tz)
        return (now_local - timedelta(days=1)).date()
