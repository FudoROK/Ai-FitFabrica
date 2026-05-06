from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Literal

RollingArtifactsWriteErrorCode = Literal[
    "write_rejected",
    "idempotency_conflict_rolling",
    "rolling_base_conflict",
]

_RETRYABLE_BY_CODE: dict[RollingArtifactsWriteErrorCode, bool] = {
    "write_rejected": True,
    "idempotency_conflict_rolling": False,
    "rolling_base_conflict": False,
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RollingArtifactsWriteRequest:
    lead_id: str
    local_day_key: str
    job_type: str
    updated_at: datetime
    rolling_update: dict[str, object]
    previous_rolling_payload: dict[str, object] | None = None
    conversation_state_update: dict | None = None

    @property
    def idempotency_key(self) -> str:
        return f"{self.lead_id}:{self.local_day_key}:{self.job_type}:rolling"


@dataclass(frozen=True)
class RollingArtifactsWriteResult:
    status: Literal["applied", "rejected", "conflict"]
    idempotency_key: str
    error_code: RollingArtifactsWriteErrorCode | None = None
    retryable: bool = False
    rolling_written: bool = False
    conversation_written: bool = False


class RollingArtifactsWriteUseCase:
    """Write policy boundary for rolling artifacts and conversation state."""

    def __init__(self, *, persistence_service) -> None:
        self.persistence_service = persistence_service

    async def execute(self, *, request: RollingArtifactsWriteRequest) -> RollingArtifactsWriteResult:
        if not request.lead_id or not request.local_day_key or not request.job_type:
            return self._rejected(request=request, code="write_rejected")
        if not isinstance(request.rolling_update, dict):
            return self._rejected(request=request, code="write_rejected")

        guard_acquired = await self.persistence_service.acquire_memory_write_guard(
            lead_id=request.lead_id,
            idempotency_key=request.idempotency_key,
            created_at=request.updated_at,
        )
        if not guard_acquired:
            logger.info(
                "rolling_artifacts_idempotency_conflict",
                extra={"idempotency_key": request.idempotency_key},
            )
            return RollingArtifactsWriteResult(
                status="conflict",
                idempotency_key=request.idempotency_key,
                error_code="idempotency_conflict_rolling",
                retryable=False,
            )

        if not await self._matches_previous_rolling_payload(
            lead_id=request.lead_id,
            previous_rolling_payload=request.previous_rolling_payload,
        ):
            await self.persistence_service.release_memory_write_guard(
                lead_id=request.lead_id,
                idempotency_key=request.idempotency_key,
            )
            return RollingArtifactsWriteResult(
                status="conflict",
                idempotency_key=request.idempotency_key,
                error_code="rolling_base_conflict",
                retryable=False,
            )

        rolling_written = await self.persistence_service.update_rolling_summary(
            lead_id=request.lead_id,
            rolling_update=request.rolling_update,
        )
        if not rolling_written:
            await self.persistence_service.release_memory_write_guard(
                lead_id=request.lead_id,
                idempotency_key=request.idempotency_key,
            )
            return self._rejected(request=request, code="write_rejected")

        conversation_written = False
        if request.conversation_state_update is not None:
            await self.persistence_service.apply_conversation_state_update(
                lead_id=request.lead_id,
                conversation_state_update=request.conversation_state_update,
                updated_at=request.updated_at,
            )
            conversation_written = True

        return RollingArtifactsWriteResult(
            status="applied",
            idempotency_key=request.idempotency_key,
            retryable=False,
            rolling_written=True,
            conversation_written=conversation_written,
        )

    async def _matches_previous_rolling_payload(
        self,
        *,
        lead_id: str,
        previous_rolling_payload: dict[str, object] | None,
    ) -> bool:
        if previous_rolling_payload is None:
            return True
        context = await self.persistence_service.load_lead_context(lead_id=lead_id, include_rolling=True)
        current = context.rolling_payload
        if current is None:
            return False
        return dict(current) == dict(previous_rolling_payload)

    def _rejected(self, *, request: RollingArtifactsWriteRequest, code: RollingArtifactsWriteErrorCode) -> RollingArtifactsWriteResult:
        return RollingArtifactsWriteResult(
            status="rejected",
            idempotency_key=request.idempotency_key,
            error_code=code,
            retryable=_RETRYABLE_BY_CODE[code],
        )


__all__ = [
    "RollingArtifactsWriteErrorCode",
    "RollingArtifactsWriteRequest",
    "RollingArtifactsWriteResult",
    "RollingArtifactsWriteUseCase",
]
