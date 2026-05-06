"""Per-lead memory synchronization orchestrator (Daily -> persist -> Rolling)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract
from src.runtime_agents.memory_agent.contracts.rolling import RollingMemoryContract
from src.memory_layer.domain import MemoryRunResult, MemoryRunStageDetail
from src.memory_layer.services.memory_run_ledger_service import MemoryRunLedgerService
from src.memory_layer.services.memory_sync_persistence_service import LeadMemoryContext, MemorySyncPersistenceService
from src.memory_layer.services.memory_sync_repository_contract import MemorySyncLeadRepository
from src.memory_layer.use_cases.apply_daily_agent_output_use_case import ApplyDailyAgentOutputUseCase
from src.memory_layer.use_cases.apply_rolling_memory_agent_output_use_case import ApplyRollingMemoryAgentOutputUseCase
from src.memory_layer.use_cases.process_daily_agent_output_use_case import ProcessDailyAgentOutputUseCase
from src.memory_layer.use_cases.process_rolling_memory_agent_output_use_case import ProcessRollingMemoryAgentOutputUseCase
from src.services.crm.crm_memory_sync_service import CrmMemorySyncService
from src.services.runtime.feature_flags import FeatureFlags

from .memory_sync_llm_service import MemorySummaryService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailySummaryPreparationResult:
    ready_for_processing: bool
    error_code: str | None
    messages: list[dict]
    raw_output: DailyMemoryContract | None


@dataclass(frozen=True)
class RollingUpdatePreparationResult:
    ready_for_processing: bool
    error_code: str | None
    raw_output: RollingMemoryContract | None


class MemorySyncPort:
    """Canonical memory orchestration boundary.

    scheduler_daily -> Daily invoke -> Daily validate -> Daily persist ->
    Rolling invoke -> Rolling validate -> Rolling persist -> CRM sync
    """

    def __init__(
        self,
        *,
        leads_repo: MemorySyncLeadRepository,
        memory_summary_service: MemorySummaryService,
        persistence_service: MemorySyncPersistenceService,
        crm_memory_sync_service: CrmMemorySyncService | None,
        process_daily_agent_output_use_case: ProcessDailyAgentOutputUseCase,
        apply_daily_agent_output_use_case: ApplyDailyAgentOutputUseCase,
        process_rolling_agent_output_use_case: ProcessRollingMemoryAgentOutputUseCase,
        apply_rolling_agent_output_use_case: ApplyRollingMemoryAgentOutputUseCase,
        memory_run_ledger_service: MemoryRunLedgerService,
        feature_flags: FeatureFlags,
        allow_test_process_use_case_override: bool = False,
        test_mode: bool = False,
        unsafe_override: bool = False,
        runtime_settings=None,
    ) -> None:
        _ = (allow_test_process_use_case_override, test_mode, unsafe_override, runtime_settings)
        self.feature_flags = feature_flags
        self.leads_repo = leads_repo
        self.persistence_service = persistence_service
        self.memory_summary_service = memory_summary_service
        self.crm_memory_sync_service = crm_memory_sync_service
        self.process_daily_agent_output_use_case = process_daily_agent_output_use_case
        self.apply_daily_agent_output_use_case = apply_daily_agent_output_use_case
        self.process_rolling_agent_output_use_case = process_rolling_agent_output_use_case
        self.apply_rolling_agent_output_use_case = apply_rolling_agent_output_use_case
        self.memory_run_ledger_service = memory_run_ledger_service

    async def process_lead_daily_summary(
        self,
        *,
        lead_id: str,
        start_utc: datetime,
        end_utc: datetime,
        memory_day_key: str,
        errors: list[str],
    ) -> MemoryRunResult:
        correlation_id = self._build_memory_run_correlation_id(lead_id=lead_id, memory_day_key=memory_day_key)
        stage_details: list[MemoryRunStageDetail] = []

        def stage(event: str, stage_name: str, reason: str | None = None) -> None:
            stage_details.append(
                MemoryRunStageDetail(
                    stage=stage_name,
                    status=event.replace("stage_", ""),
                    event=event,  # type: ignore[arg-type]
                    reason_code=reason,
                )
            )

        if not lead_id:
            stage("stage_failed", "entry", "invalid_lead_id")
            return self._build_result(
                outcome="failed",
                reason_code="invalid_lead_id",
                lead_id="unknown",
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
            )

        stage("stage_started", "load_context")
        context = await self._load_lead(lead_id=lead_id)
        if context is None:
            stage("stage_failed", "load_context", "lead_context_unavailable")
            return self._build_result(
                outcome="failed",
                reason_code="lead_context_unavailable",
                lead_id=lead_id,
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
            )
        stage("stage_completed", "load_context")

        # Daily
        stage("stage_started", "daily_prepare")
        daily_prepared = await self._prepare_daily_summary_bundle(
            lead_id=lead_id,
            correlation_id=correlation_id,
            context=context,
            start_utc=start_utc,
            end_utc=end_utc,
        )
        if not daily_prepared.ready_for_processing or daily_prepared.raw_output is None:
            reason = daily_prepared.error_code or "daily_prepare_failed"
            stage("stage_failed", "daily_prepare", reason)
            errors.append(f"{lead_id}:{reason}")
            return self._build_result(
                outcome="failed",
                reason_code=reason,
                lead_id=lead_id,
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
            )
        stage("stage_completed", "daily_prepare")

        stage("stage_started", "daily_process")
        daily_processed = self.process_daily_agent_output_use_case.execute(
            payload=daily_prepared.raw_output,
            correlation_id=correlation_id,
        )
        if not daily_processed.accepted or daily_processed.output is None:
            reason = daily_processed.error_code or "daily_process_rejected"
            stage("stage_rejected", "daily_process", reason)
            errors.append(f"{lead_id}:{reason}")
            return self._build_result(
                outcome="rejected",
                reason_code=reason,
                lead_id=lead_id,
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
            )
        stage("stage_completed", "daily_process")

        stage("stage_started", "daily_apply")
        daily_applied = await self.apply_daily_agent_output_use_case.execute(
            lead=context.lead_data,
            output=daily_processed.output,
            lead_id=lead_id,
            memory_day_key=memory_day_key,
            start_utc=start_utc,
            end_utc=end_utc,
            messages=daily_prepared.messages,
            job_type="memory_daily_sync_task",
        )
        if daily_applied.write_status != "applied":
            reason = daily_applied.write_error_code or "daily_write_rejected"
            stage("stage_failed", "daily_apply", reason)
            errors.append(f"{lead_id}:{reason}")
            return self._build_result(
                outcome="failed",
                reason_code=reason,
                lead_id=lead_id,
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
                daily_written=daily_applied.daily_written,
                apply_completed=daily_applied.daily_written,
                write_status=daily_applied.write_status,
                write_error_code=daily_applied.write_error_code,
            )
        stage("stage_completed", "daily_apply")

        # Rolling
        stage("stage_started", "rolling_prepare")
        rolling_prepared = await self._prepare_rolling_update_bundle(
            lead_id=lead_id,
            correlation_id=correlation_id,
            context=context,
            daily_output=daily_processed.output,
            memory_day_key=memory_day_key,
        )
        if not rolling_prepared.ready_for_processing or rolling_prepared.raw_output is None:
            reason = rolling_prepared.error_code or "rolling_prepare_failed"
            stage("stage_failed", "rolling_prepare", reason)
            errors.append(f"{lead_id}:{reason}")
            return self._build_result(
                outcome="failed",
                reason_code=reason,
                lead_id=lead_id,
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
                daily_written=True,
                apply_completed=True,
                write_status="partial",
            )
        stage("stage_completed", "rolling_prepare")

        stage("stage_started", "rolling_process")
        rolling_processed = self.process_rolling_agent_output_use_case.execute(
            payload=rolling_prepared.raw_output,
            correlation_id=correlation_id,
        )
        if not rolling_processed.accepted or rolling_processed.output is None:
            reason = rolling_processed.error_code or "rolling_process_rejected"
            stage("stage_rejected", "rolling_process", reason)
            errors.append(f"{lead_id}:{reason}")
            return self._build_result(
                outcome="rejected",
                reason_code=reason,
                lead_id=lead_id,
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
                daily_written=True,
                apply_completed=True,
                write_status="partial",
            )
        stage("stage_completed", "rolling_process")

        stage("stage_started", "rolling_apply")
        rolling_applied = await self.apply_rolling_agent_output_use_case.execute(
            output=rolling_processed.output,
            lead_id=lead_id,
            memory_day_key=memory_day_key,
            updated_at=end_utc,
            job_type="memory_rolling_sync_task",
        )
        if rolling_applied.write_status != "applied":
            reason = rolling_applied.write_error_code or "rolling_write_rejected"
            stage("stage_failed", "rolling_apply", reason)
            errors.append(f"{lead_id}:{reason}")
            return self._build_result(
                outcome="failed",
                reason_code=reason,
                lead_id=lead_id,
                correlation_id=correlation_id,
                memory_day_key=memory_day_key,
                stage_details=stage_details,
                daily_written=True,
                rolling_written=rolling_applied.rolling_written,
                apply_completed=True,
                write_status="partial",
                write_error_code=rolling_applied.write_error_code,
            )
        stage("stage_completed", "rolling_apply")

        stage("stage_started", "crm_sync")
        crm_ok = await self._sync_crm_after_memory_commit(
            lead_id=lead_id,
            lead_data=context.lead_data,
            daily_summary_text=daily_applied.daily_summary_text,
            memory_day_key=memory_day_key,
            errors=errors,
        )
        stage("stage_completed", "crm_sync", None if crm_ok else "crm_sync_skipped_or_failed")

        return self._build_result(
            outcome="success",
            reason_code=None,
            lead_id=lead_id,
            correlation_id=correlation_id,
            memory_day_key=memory_day_key,
            stage_details=stage_details,
            daily_written=True,
            rolling_written=True,
            apply_completed=True,
            crm_synced=crm_ok,
            write_status="applied",
        )

    async def _prepare_daily_summary_bundle(
        self,
        *,
        lead_id: str,
        correlation_id: str,
        context: LeadMemoryContext,
        start_utc: datetime,
        end_utc: datetime,
    ) -> DailySummaryPreparationResult:
        messages = await self.persistence_service.fetch_messages(
            lead_id=lead_id,
            start_utc=start_utc,
            end_utc=end_utc,
        )
        if not messages:
            return DailySummaryPreparationResult(
                ready_for_processing=False,
                error_code="messages_not_found",
                messages=[],
                raw_output=None,
            )

        extraction_result = await self.memory_summary_service.generate_memory_output(
            lead_id=lead_id,
            correlation_id=correlation_id,
            lead_profile=context.lead_profile,
            active_window=context.active_window,
            conversation_state=context.conversation_state,
            messages=messages,
        )
        return DailySummaryPreparationResult(
            ready_for_processing=extraction_result.output is not None,
            error_code=extraction_result.error_code,
            messages=messages,
            raw_output=extraction_result.output,
        )

    async def _prepare_rolling_update_bundle(
        self,
        *,
        lead_id: str,
        correlation_id: str,
        context: LeadMemoryContext,
        daily_output: DailyMemoryContract,
        memory_day_key: str,
    ) -> RollingUpdatePreparationResult:
        extraction_result = await self.memory_summary_service.generate_rolling_update(
            lead_id=lead_id,
            correlation_id=correlation_id,
            prior_rolling_memory=context.rolling_payload,
            new_daily_summary={
                "memory_day_key": memory_day_key,
                **daily_output.daily_summary.model_dump(mode="python", exclude_none=True),
            },
        )
        return RollingUpdatePreparationResult(
            ready_for_processing=extraction_result.output is not None,
            error_code=extraction_result.error_code,
            raw_output=extraction_result.output,
        )

    async def _load_lead(self, *, lead_id: str) -> Optional[LeadMemoryContext]:
        try:
            return await self.persistence_service.load_lead_context(lead_id=lead_id, include_rolling=True)
        except Exception:  # pragma: no cover - defensive
            logger.exception("memory_load_lead_context_failed", extra={"lead_id": lead_id})
            return None

    async def _sync_crm_after_memory_commit(
        self,
        *,
        lead_id: str,
        lead_data: dict,
        daily_summary_text: str,
        memory_day_key: str,
        errors: list[str],
    ) -> bool:
        if self.crm_memory_sync_service is None:
            return False

        confirmed = await self.persistence_service.fetch_confirmed_rolling_summary_validation(lead_id=lead_id)
        if not confirmed.ok:
            errors.append(f"{lead_id}:{confirmed.reason_code}")
            return False

        crm_result = await self.crm_memory_sync_service.sync_memory(
            lead_id=lead_id,
            lead_data=lead_data,
            daily_summary=daily_summary_text,
            daily_date=memory_day_key,
            rolling_summary=confirmed.normalized_text,
            rolling_version=confirmed.rolling_version,
            rolling_hash=confirmed.rolling_hash,
            errors=errors,
        )
        return bool(crm_result.ok)

    @staticmethod
    def _build_memory_run_correlation_id(*, lead_id: str, memory_day_key: str) -> str:
        return f"memory:{lead_id}:{memory_day_key}:{uuid4().hex[:10]}"

    @staticmethod
    def _build_result(
        *,
        outcome: str,
        reason_code: str | None,
        lead_id: str,
        correlation_id: str,
        memory_day_key: str,
        stage_details: list[MemoryRunStageDetail],
        daily_written: bool = False,
        rolling_written: bool = False,
        apply_completed: bool = False,
        crm_synced: bool = False,
        write_status: str | None = None,
        write_error_code: str | None = None,
    ) -> MemoryRunResult:
        return MemoryRunResult(
            outcome=outcome,  # type: ignore[arg-type]
            reason_code=reason_code,
            lead_id=lead_id,
            correlation_id=correlation_id,
            local_day_key=memory_day_key,
            stage_details=tuple(stage_details),
            idempotency_key=f"{lead_id}:{memory_day_key}:memory_daily_scheduler",
            write_status=write_status,
            write_error_code=write_error_code,
            daily_written=daily_written,
            rolling_written=rolling_written,
            apply_completed=apply_completed,
            crm_synced=crm_synced,
            partial_effect_detected=daily_written and not rolling_written,
            recovered=False,
        )
