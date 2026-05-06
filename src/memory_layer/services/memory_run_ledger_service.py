from __future__ import annotations

from datetime import datetime, timezone

from src.memory_layer.domain.memory_run_ledger import MemoryRunIntent
from src.memory_layer.run_ledger_repository import (
    MemoryRunBeginDecision,
)


class MemoryRunLedgerService:
    def __init__(self, *, repository, pipeline_version: str = "scheduler_daily_v1") -> None:
        self.repository = repository
        self.pipeline_version = pipeline_version

    def build_intent(
        self,
        *,
        lead_id: str,
        local_day_key: str,
        window_id: str,
    ) -> MemoryRunIntent:
        return MemoryRunIntent(
            lead_id=lead_id,
            local_day_key=local_day_key,
            window_id=window_id,
            pipeline_version=self.pipeline_version,
        )

    async def begin_attempt(self, *, intent: MemoryRunIntent, now: datetime | None = None) -> MemoryRunBeginDecision:
        observed_now = now or datetime.now(tz=timezone.utc)
        return await self.repository.begin_attempt(intent=intent, now=observed_now)

    async def mark_stage(
        self,
        *,
        intent_id: str,
        stage: str,
        status: str,
        reason_code: str | None = None,
        rolling_version: int | None = None,
        rolling_hash: str | None = None,
        artifact_id: str | None = None,
        now: datetime | None = None,
    ):
        observed_now = now or datetime.now(tz=timezone.utc)
        return await self.repository.mark_stage(
            intent_id=intent_id,
            stage=stage,
            status=status,
            reason_code=reason_code,
            rolling_version=rolling_version,
            rolling_hash=rolling_hash,
            artifact_id=artifact_id,
            now=observed_now,
        )

    async def mark_partial_effect(
        self,
        *,
        intent_id: str,
        reason_code: str,
        now: datetime | None = None,
    ):
        observed_now = now or datetime.now(tz=timezone.utc)
        return await self.repository.mark_partial_effect(intent_id=intent_id, now=observed_now, reason_code=reason_code)

    async def finalize(
        self,
        *,
        intent_id: str,
        final_outcome: str,
        reason_code: str | None,
        conflict_class: str | None,
        partial_effect_detected: bool,
        recovered: bool,
        now: datetime | None = None,
    ):
        observed_now = now or datetime.now(tz=timezone.utc)
        return await self.repository.finalize(
            intent_id=intent_id,
            final_outcome=final_outcome,
            reason_code=reason_code,
            conflict_class=conflict_class,
            partial_effect_detected=partial_effect_detected,
            recovered=recovered,
            now=observed_now,
        )


__all__ = ["MemoryRunLedgerService"]
