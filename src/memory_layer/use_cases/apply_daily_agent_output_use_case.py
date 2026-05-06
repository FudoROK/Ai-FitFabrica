from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract
from .daily_artifacts_write_use_case import DailyArtifactsWriteRequest, DailyArtifactsWriteUseCase


@dataclass(frozen=True)
class ApplyDailyAgentOutputResult:
    daily_summary_text: str
    daily_summary_payload: dict[str, object]
    daily_written: bool
    write_status: str
    write_error_code: str | None = None
    retryable: bool = False


class ApplyDailyAgentOutputUseCase:
    def __init__(
        self,
        *,
        persistence_service,
        daily_write_use_case: DailyArtifactsWriteUseCase | None = None,
    ) -> None:
        self.persistence_service = persistence_service
        self.daily_write_use_case = daily_write_use_case or DailyArtifactsWriteUseCase(persistence_service=persistence_service)
        # rolling_write_use_case removed as per new architecture


    async def execute(
        self,
        *,
        lead,
        output: DailyMemoryContract,
        lead_id: str,
        memory_day_key: str,
        start_utc: datetime,
        end_utc: datetime,
        messages: list[dict],
        job_type: str = "memory_daily_sync_task",
        run_intent_id: str | None = None,
    ) -> ApplyDailyAgentOutputResult:
        daily_payload = self.persistence_service.build_daily_summary_payload(
            memory_day_key=memory_day_key,
            daily_summary_payload=output.daily_summary.model_dump(mode="python", exclude_none=True),
            messages=messages,
            start_utc=start_utc,
            end_utc=end_utc,
        )

        daily_write_result = await self.daily_write_use_case.execute(
            request=DailyArtifactsWriteRequest(
                lead_id=lead_id,
                local_day_key=memory_day_key,
                job_type=job_type,
                updated_at=end_utc,
                daily_payload=daily_payload,
            )
        )

        if daily_write_result.status == "applied":
            await self.persistence_service.apply_memory_agent_updates(
                lead=lead,
                active_window_update=output.active_window_update.model_dump(mode="python", exclude_none=True)
                if output.active_window_update is not None
                else None,
                conversation_state_update=output.conversation_state_update.model_dump(mode="python", exclude_none=True)
                if output.conversation_state_update is not None
                else None,
                updated_at=end_utc,
            )

        return ApplyDailyAgentOutputResult(
            daily_summary_text=output.daily_summary.summary_text,
            daily_summary_payload=daily_payload,
            daily_written=daily_write_result.daily_written,
            write_status=daily_write_result.status,
            write_error_code=daily_write_result.error_code,
            retryable=daily_write_result.retryable,
        )
