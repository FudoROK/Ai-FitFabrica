from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.runtime_agents.memory_agent.contracts.rolling import RollingMemoryContract
from .rolling_artifacts_write_use_case import RollingArtifactsWriteRequest, RollingArtifactsWriteUseCase


@dataclass(frozen=True)
class ApplyRollingMemoryAgentOutputResult:
    rolling_summary_text: str
    rolling_update_payload: dict[str, object]
    rolling_written: bool
    write_status: str
    write_error_code: str | None = None
    retryable: bool = False


class ApplyRollingMemoryAgentOutputUseCase:
    def __init__(
        self,
        *,
        persistence_service,
        rolling_write_use_case: RollingArtifactsWriteUseCase | None = None,
    ) -> None:
        self.persistence_service = persistence_service
        self.rolling_write_use_case = rolling_write_use_case or RollingArtifactsWriteUseCase(persistence_service=persistence_service)


    async def execute(
        self,
        *,
        output: RollingMemoryContract,
        lead_id: str,
        memory_day_key: str,
        updated_at: datetime,
        job_type: str = "memory_rolling_sync_task",
        conversation_state_update: dict[str, object] | None = None,
    ) -> ApplyRollingMemoryAgentOutputResult:

        rolling_update_payload = output.rolling_update.model_dump(mode="python", exclude_none=True)

        rolling_write_result = await self.rolling_write_use_case.execute(
            request=RollingArtifactsWriteRequest(
                lead_id=lead_id,
                local_day_key=memory_day_key,
                job_type=job_type,
                updated_at=updated_at,
                rolling_update=rolling_update_payload,
                conversation_state_update=conversation_state_update,
            )
        )

        return ApplyRollingMemoryAgentOutputResult(
            rolling_summary_text=output.rolling_update.rolling_summary_text,
            rolling_update_payload=rolling_update_payload,
            rolling_written=rolling_write_result.rolling_written,
            write_status=rolling_write_result.status,
            write_error_code=rolling_write_result.error_code,
            retryable=rolling_write_result.retryable,
        )
