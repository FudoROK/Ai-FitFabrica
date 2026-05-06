from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Literal

MemoryConflictClass = Literal[
    "duplicate_complete",
    "conflict_in_progress",
    "idempotency_conflict",
    "rolling_base_conflict",
    "conflict_unknown",
]

MemoryStageStatus = Literal[
    "started",
    "completed",
    "skipped",
    "rejected",
    "failed",
]

MemoryFinalOutcome = Literal[
    "success",
    "rejected",
    "skipped",
    "idempotent_noop",
    "failed",
]


@dataclass(frozen=True)
class MemoryRunIntent:
    lead_id: str
    local_day_key: str
    window_id: str
    pipeline_version: str

    @property
    def intent_id(self) -> str:
        payload = "|".join((self.lead_id, self.local_day_key, self.window_id, self.pipeline_version))
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MemoryRunAttemptRecord:
    attempt_no: int
    run_id: str
    started_at: datetime
    ended_at: datetime | None = None
    outcome: MemoryFinalOutcome | None = None
    reason_code: str | None = None
    reentry_reason: str | None = None


@dataclass
class MemoryRunLedgerState:
    intent_id: str
    run_id: str
    attempt_no: int
    lead_id: str
    local_day_key: str
    window_id: str
    pipeline_version: str
    current_stage: str | None
    stage_statuses: dict[str, MemoryStageStatus] = field(default_factory=dict)
    stage_reason_codes: dict[str, str] = field(default_factory=dict)
    final_outcome: MemoryFinalOutcome | None = None
    reason_code: str | None = None
    rolling_version: int | None = None
    rolling_hash: str | None = None
    artifact_id: str | None = None
    conflict_class: MemoryConflictClass | None = None
    partial_effect_detected: bool = False
    recovered: bool = False
    in_progress: bool = False
    reentry_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_attempt_started_at: datetime | None = None
    last_attempt_finished_at: datetime | None = None
    attempt_history: list[MemoryRunAttemptRecord] = field(default_factory=list)


__all__ = [
    "MemoryConflictClass",
    "MemoryFinalOutcome",
    "MemoryRunAttemptRecord",
    "MemoryRunIntent",
    "MemoryRunLedgerState",
    "MemoryStageStatus",
]
