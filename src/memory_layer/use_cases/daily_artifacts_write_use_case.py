from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Literal

from src.memory_layer.services.memory_sync_persistence_service import DailySummaryWritePayload

DailyArtifactsWriteErrorCode = Literal[
    "write_rejected",
    "idempotency_conflict_daily",
    "daily_payload_conflict",
]

_RETRYABLE_BY_CODE: dict[DailyArtifactsWriteErrorCode, bool] = {
    "write_rejected": True,
    "idempotency_conflict_daily": False,
    "daily_payload_conflict": False,
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailyArtifactsWriteRequest:
    lead_id: str
    local_day_key: str
    job_type: str
    updated_at: datetime
    daily_payload: DailySummaryWritePayload

    @property
    def idempotency_key(self) -> str:
        return f"{self.lead_id}:{self.local_day_key}:{self.job_type}:daily"


@dataclass(frozen=True)
class DailyArtifactsWriteResult:
    status: Literal["applied", "rejected", "conflict"]
    idempotency_key: str
    error_code: DailyArtifactsWriteErrorCode | None = None
    retryable: bool = False
    daily_written: bool = False


class DailyArtifactsWriteUseCase:
    """Write policy boundary for daily artifacts only."""

    def __init__(self, *, persistence_service) -> None:
        self.persistence_service = persistence_service

    async def execute(self, *, request: DailyArtifactsWriteRequest) -> DailyArtifactsWriteResult:
        if not request.lead_id or not request.local_day_key or not request.job_type:
            return self._rejected(request=request, code="write_rejected")

        guard_acquired = await self.persistence_service.acquire_memory_write_guard(
            lead_id=request.lead_id,
            idempotency_key=request.idempotency_key,
            created_at=request.updated_at,
        )
        if not guard_acquired:
            logger.info(
                "daily_artifacts_idempotency_conflict",
                extra={"idempotency_key": request.idempotency_key},
            )
            return DailyArtifactsWriteResult(
                status="conflict",
                idempotency_key=request.idempotency_key,
                error_code="idempotency_conflict_daily",
                retryable=False,
            )

        written = await self.persistence_service.write_daily_summary(
            lead_id=request.lead_id,
            payload=request.daily_payload,
        )
        if written:
            return DailyArtifactsWriteResult(
                status="applied",
                idempotency_key=request.idempotency_key,
                retryable=False,
                daily_written=True,
            )

        await self.persistence_service.release_memory_write_guard(
            lead_id=request.lead_id,
            idempotency_key=request.idempotency_key,
        )
        return DailyArtifactsWriteResult(
            status="conflict",
            idempotency_key=request.idempotency_key,
            error_code="daily_payload_conflict",
            retryable=False,
            daily_written=False,
        )

    def _rejected(self, *, request: DailyArtifactsWriteRequest, code: DailyArtifactsWriteErrorCode) -> DailyArtifactsWriteResult:
        return DailyArtifactsWriteResult(
            status="rejected",
            idempotency_key=request.idempotency_key,
            error_code=code,
            retryable=_RETRYABLE_BY_CODE[code],
        )


__all__ = [
    "DailyArtifactsWriteErrorCode",
    "DailyArtifactsWriteRequest",
    "DailyArtifactsWriteResult",
    "DailyArtifactsWriteUseCase",
]
