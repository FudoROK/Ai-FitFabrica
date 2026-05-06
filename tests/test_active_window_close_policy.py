from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.memory_layer.domain.memory_run_outcome import MemoryRunResult
from src.memory_layer.domain.window_close_policy import WindowClosePolicy
from src.memory_layer.models import ActiveWindowRecord
from src.memory_layer.services.memory_summary_service import MemorySummaryService


class _FakeMemoryLayerService:
    def __init__(self, window: ActiveWindowRecord | list[ActiveWindowRecord]) -> None:
        self._windows = window if isinstance(window, list) else [window]
        self.closed_calls = 0

    async def list_active_windows(self, *, statuses=None):
        return list(self._windows)

    async def get_active_window(self, *, lead_id: str):
        for window in self._windows:
            if window.lead_id == lead_id:
                return window
        return None

    async def refresh_active_window_lifecycle(self, *, lead, as_of: datetime):
        _ = lead, as_of
        for window in self._windows:
            if window.lead_id == getattr(lead, "lead_id", None):
                return window
        return None

    async def close_active_window(self, *, lead, closed_at: datetime):
        _ = lead, closed_at
        self.closed_calls += 1
        return await self.get_active_window(lead_id=getattr(lead, "lead_id", ""))


class _FakeLeadsRepo:
    async def get(self, lead_id: str):
        return SimpleNamespace(lead_id=lead_id, timezone="UTC")


class _FakeSyncPort:
    def __init__(
        self,
        fail_lead_ids: set[str] | None = None,
        skip_conflict_lead_ids: set[str] | None = None,
    ) -> None:
        self.fail_lead_ids = fail_lead_ids or set()
        self.skip_conflict_lead_ids = skip_conflict_lead_ids or set()

    async def process_lead_daily_summary(self, **kwargs):
        if kwargs.get("lead_id") in self.fail_lead_ids:
            return MemoryRunResult(
                outcome="failed",
                reason_code="sync_failed",
                lead_id=str(kwargs.get("lead_id")),
                correlation_id="corr-failed",
                local_day_key=str(kwargs.get("memory_day_key")),
                stage_details=(),
            )
        if kwargs.get("lead_id") in self.skip_conflict_lead_ids:
            return MemoryRunResult(
                outcome="skipped",
                reason_code="conflict_in_progress",
                conflict_class="conflict_in_progress",
                lead_id=str(kwargs.get("lead_id")),
                correlation_id="corr-conflict",
                local_day_key=str(kwargs.get("memory_day_key")),
                stage_details=(),
            )
        return MemoryRunResult(
            outcome="skipped",
            reason_code="no_messages",
            lead_id=str(kwargs.get("lead_id")),
            correlation_id="corr-skipped",
            local_day_key=str(kwargs.get("memory_day_key")),
            stage_details=(),
        )


def _summary_service_settings(*, batch_limit: int | None = None) -> SimpleNamespace:
    data = {
        "memory_summary_enabled": True,
        "memory_summary_timezone": "UTC",
    }
    if batch_limit is not None:
        data["memory_summary_batch_limit"] = batch_limit
    return SimpleNamespace(**data)


def _build_service(
    *,
    windows: ActiveWindowRecord | list[ActiveWindowRecord],
    batch_limit: int | None = None,
    sync_port: _FakeSyncPort | None = None,
) -> MemorySummaryService:
    service = MemorySummaryService.__new__(MemorySummaryService)
    service.firestore = object()
    service.settings = _summary_service_settings(batch_limit=batch_limit)
    service.memory_layer_service = _FakeMemoryLayerService(windows)
    service.leads_repo = _FakeLeadsRepo()
    service.sync_port = sync_port or _FakeSyncPort()
    return service


def test_window_close_policy_uses_configured_local_cutoff_only():
    opened_at = datetime(2026, 4, 13, 0, 10, tzinfo=timezone.utc)
    last_activity_at = opened_at + timedelta(minutes=40)

    timing = WindowClosePolicy.resolve(
        opened_at=opened_at,
        last_activity_at=last_activity_at,
        timezone_name="UTC",
        cutoff_hour=0,
        cutoff_minute=58,
        grace_period=timedelta(minutes=1),
    )

    assert timing.window_close_at_utc == datetime(2026, 4, 13, 0, 58, tzinfo=timezone.utc)
    assert timing.close_threshold_utc == timing.window_close_at_utc
    assert timing.grace_until_utc == timing.window_close_at_utc


@pytest.mark.anyio
async def test_closing_window_is_closed_even_when_summary_not_updated():
    opened_at = datetime(2026, 4, 12, 1, 0, tzinfo=timezone.utc)
    window = ActiveWindowRecord(
        lead_id="telegram:42",
        timezone="UTC",
        local_day_key="2026-04-12",
        window_status="closing",
        opened_at=opened_at,
        last_activity_at=opened_at,
        updated_at=opened_at,
    )

    service = _build_service(windows=window)

    result = await service.run_daily_summary_job()

    assert result.leads_processed == 1
    assert result.summaries_written == 0
    assert service.memory_layer_service.closed_calls == 1


@pytest.mark.anyio
async def test_batch_mode_applies_limit_and_collects_failed_leads():
    opened_at = datetime(2026, 4, 12, 1, 0, tzinfo=timezone.utc)
    windows = [
        ActiveWindowRecord(
            lead_id="telegram:1",
            timezone="UTC",
            local_day_key="2026-04-12",
            window_status="closing",
            opened_at=opened_at,
            last_activity_at=opened_at,
            updated_at=opened_at,
        ),
        ActiveWindowRecord(
            lead_id="telegram:2",
            timezone="UTC",
            local_day_key="2026-04-12",
            window_status="closing",
            opened_at=opened_at,
            last_activity_at=opened_at,
            updated_at=opened_at,
        ),
    ]

    service = _build_service(
        windows=windows,
        batch_limit=1,
        sync_port=_FakeSyncPort(fail_lead_ids={"telegram:1"}),
    )

    result = await service.run_daily_summary_job()

    assert result.total_selected == 2
    assert result.total_processed == 1
    assert result.total_failed == 1
    assert result.failed_leads == [{"lead_id": "telegram:1", "reason": "sync_failed"}]


@pytest.mark.anyio
async def test_window_not_closed_for_conflict_skip_outcome():
    opened_at = datetime(2026, 4, 12, 1, 0, tzinfo=timezone.utc)
    window = ActiveWindowRecord(
        lead_id="telegram:99",
        timezone="UTC",
        local_day_key="2026-04-12",
        window_status="closing",
        opened_at=opened_at,
        last_activity_at=opened_at,
        updated_at=opened_at,
    )

    service = _build_service(
        windows=window,
        sync_port=_FakeSyncPort(skip_conflict_lead_ids={"telegram:99"}),
    )

    result = await service.run_daily_summary_job()

    assert result.leads_processed == 1
    assert service.memory_layer_service.closed_calls == 0