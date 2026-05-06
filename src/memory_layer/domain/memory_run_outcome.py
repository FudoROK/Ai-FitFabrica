from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from .memory_run_ledger import MemoryFinalOutcome, MemoryStageStatus

MemoryRunOutcomeType: TypeAlias = MemoryFinalOutcome

MemoryRunStageEvent = Literal[
    "stage_started",
    "stage_completed",
    "stage_skipped",
    "stage_rejected",
    "stage_failed",
    "final_outcome",
]

MemoryRunStageStatus: TypeAlias = MemoryStageStatus


@dataclass(frozen=True)
class MemoryRunStageDetail:
    stage: str
    status: MemoryRunStageStatus
    event: MemoryRunStageEvent
    reason_code: str | None = None
    rolling_version: int | None = None
    rolling_hash: str | None = None
    artifact_id: str | None = None
    artifact_path: str | None = None
    pointer_id: str | None = None
    pointer_path: str | None = None


@dataclass(frozen=True)
class MemoryRunResult:
    outcome: MemoryRunOutcomeType
    reason_code: str | None
    lead_id: str
    correlation_id: str
    local_day_key: str
    stage_details: tuple[MemoryRunStageDetail, ...]
    intent_id: str | None = None
    run_id: str | None = None
    attempt_no: int | None = None
    window_id: str | None = None
    idempotency_key: str | None = None
    reentry_reason: str | None = None
    conflict_class: str | None = None
    write_status: str | None = None
    write_error_code: str | None = None
    daily_written: bool = False
    rolling_written: bool = False
    apply_completed: bool = False
    crm_synced: bool = False
    partial_effect_detected: bool = False
    recovered: bool = False


__all__ = [
    "MemoryRunOutcomeType",
    "MemoryRunStageEvent",
    "MemoryRunStageStatus",
    "MemoryRunStageDetail",
    "MemoryRunResult",
]
