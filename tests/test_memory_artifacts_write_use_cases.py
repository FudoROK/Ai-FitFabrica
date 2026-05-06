from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from src.memory_layer.services.memory_sync_persistence_service import DailySummaryWritePayload
from src.memory_layer.use_cases.daily_artifacts_write_use_case import DailyArtifactsWriteRequest, DailyArtifactsWriteUseCase
from src.memory_layer.use_cases.rolling_artifacts_write_use_case import RollingArtifactsWriteRequest, RollingArtifactsWriteUseCase


class _PersistenceStub:
    def __init__(self) -> None:
        self.guards: set[tuple[str, str]] = set()
        self.daily_ok = True
        self.rolling_ok = True
        self.current_rolling_payload: dict[str, object] | None = None
        self.daily_calls = 0
        self.rolling_calls = 0
        self.conversation_calls = 0

    async def acquire_memory_write_guard(self, *, lead_id: str, idempotency_key: str, created_at: datetime) -> bool:
        _ = created_at
        key = (lead_id, idempotency_key)
        if key in self.guards:
            return False
        self.guards.add(key)
        return True

    async def release_memory_write_guard(self, *, lead_id: str, idempotency_key: str) -> None:
        self.guards.discard((lead_id, idempotency_key))

    async def write_daily_summary(self, *, lead_id: str, payload: DailySummaryWritePayload) -> bool:
        _ = lead_id
        _ = payload
        self.daily_calls += 1
        return self.daily_ok

    async def update_rolling_summary(self, *, lead_id: str, rolling_update: dict[str, object]) -> bool:
        _ = lead_id
        self.rolling_calls += 1
        if self.rolling_ok:
            self.current_rolling_payload = dict(rolling_update)
        return self.rolling_ok

    async def load_lead_context(self, *, lead_id: str, include_rolling: bool = True):
        _ = lead_id
        _ = include_rolling
        return type("_Ctx", (), {"rolling_payload": self.current_rolling_payload})()

    async def apply_conversation_state_update(self, *, lead_id: str, conversation_state_update: dict | None, updated_at: datetime) -> None:
        _ = lead_id
        _ = conversation_state_update
        _ = updated_at
        self.conversation_calls += 1


def _daily_request() -> DailyArtifactsWriteRequest:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return DailyArtifactsWriteRequest(
        lead_id="lead-1",
        local_day_key="2026-01-01",
        job_type="memory_daily_sync_task",
        updated_at=now,
        daily_payload=DailySummaryWritePayload(
            memory_day_key="2026-01-01",
            summary_text="daily",
            open_questions=[],
            carry_forward_notes=[],
            learned_facts=[],
            changed_facts=[],
            memory_relevance_flags=[],
            created_at=now,
            messages_used_count=2,
            source_window_start=now,
            source_window_end=now,
        ),
    )


def _rolling_request(*, previous: dict[str, object] | None = None) -> RollingArtifactsWriteRequest:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return RollingArtifactsWriteRequest(
        lead_id="lead-1",
        local_day_key="2026-01-01",
        job_type="memory_daily_sync_task",
        updated_at=now,
        rolling_update={"rolling_summary_text": "rolling", "version": 2, "days_count": 2},
        previous_rolling_payload=previous,
        conversation_state_update={"pending_question": "budget?"},
    )


def test_daily_write_use_case_uses_daily_idempotency_namespace():
    persistence = _PersistenceStub()
    use_case = DailyArtifactsWriteUseCase(persistence_service=persistence)

    first = asyncio.run(use_case.execute(request=_daily_request()))
    second = asyncio.run(use_case.execute(request=_daily_request()))

    assert first.status == "applied"
    assert second.status == "conflict"
    assert second.error_code == "idempotency_conflict_daily"


def test_rolling_write_use_case_detects_rolling_base_conflict():
    persistence = _PersistenceStub()
    persistence.current_rolling_payload = {"rolling_summary_text": "old", "version": 1}
    use_case = RollingArtifactsWriteUseCase(persistence_service=persistence)

    result = asyncio.run(
        use_case.execute(
            request=_rolling_request(previous={"rolling_summary_text": "stale", "version": 1})
        )
    )

    assert result.status == "conflict"
    assert result.error_code == "rolling_base_conflict"


def test_rolling_write_use_case_writes_rolling_and_conversation():
    persistence = _PersistenceStub()
    persistence.current_rolling_payload = {"rolling_summary_text": "v1", "version": 1}
    use_case = RollingArtifactsWriteUseCase(persistence_service=persistence)

    result = asyncio.run(
        use_case.execute(
            request=_rolling_request(previous={"rolling_summary_text": "v1", "version": 1})
        )
    )

    assert result.status == "applied"
    assert result.rolling_written is True
    assert result.conversation_written is True
    assert persistence.rolling_calls == 1
    assert persistence.conversation_calls == 1
