from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from src.memory_layer import InMemoryMemoryLayerRepository, MemoryLayerService
from src.services.context.context_projection import ContextProjectionService


class _Lead:
    def __init__(self) -> None:
        self.rolling_summary = "rolling"

    def model_dump(self, mode: str = "python") -> dict:
        assert mode == "python"
        return {"id": "lead", "stage": "warm"}


class _ProjectionRepo:
    async def get(self, lead_id: str):
        assert lead_id == "canonical-42"
        return _Lead()

    async def fetch_last_messages(self, *, lead_id: str, since, limit: int = 30):
        assert lead_id == "canonical-42"
        assert limit == 3
        assert since.tzinfo is not None
        return [
            {"text": "second", "role": "assistant", "timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc)},
            {"text": "first", "role": "user", "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc)},
            {"text": "", "role": "assistant", "timestamp": datetime(2026, 1, 3, tzinfo=timezone.utc)},
        ]

    async def fetch_latest_daily_summary(self, *, lead_id: str):
        assert lead_id == "canonical-42"
        return {"summary_text": "daily"}

    async def fetch_rolling_summary(self, *, lead_id: str):
        assert lead_id == "canonical-42"
        return {"rolling_summary_text": "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.", "days_count": 1, "version": 1, "last_daily_summary_date": "2026-01-01"}


class _FallbackRepo(_ProjectionRepo):
    async def fetch_rolling_summary(self, *, lead_id: str):
        raise RuntimeError("rolling unavailable")

    async def fetch_last_messages(self, *, lead_id: str, since, limit: int = 30):
        raise RuntimeError("messages unavailable")

    async def fetch_latest_daily_summary(self, *, lead_id: str):
        raise RuntimeError("summary unavailable")


class _ClearedRollingRepo(_ProjectionRepo):
    async def fetch_rolling_summary(self, *, lead_id: str):
        assert lead_id == "canonical-42"
        return None


class _GhostRollingRepo(_ProjectionRepo):
    async def fetch_rolling_summary(self, *, lead_id: str):
        assert lead_id == "canonical-42"
        return {"lead_id": lead_id, "updated_at": "2026-01-01T00:00:00Z"}


def test_projection_normalizes_storage_shapes_and_sorts_messages():
    memory_layer = MemoryLayerService(repository=InMemoryMemoryLayerRepository())
    service = ContextProjectionService(leads_repo=_ProjectionRepo(), memory_layer=memory_layer)

    projection = asyncio.run(
        service.project(
            lead_id="canonical-42",
            channel="telegram",
            external_user_id="42",
            chat_id="100",
            last_messages_limit=3,
        )
    )

    assert projection.identity == {
        "channel": "telegram",
        "external_user_id": "42",
        "chat_id": "100",
        "lead_id": "canonical-42",
    }
    assert projection.lead_snapshot == {"id": "lead", "stage": "warm"}
    assert projection.memory["rolling_summary"].startswith("Клиент подтвердил интерес")
    assert projection.memory["daily_summary"] == "daily"
    assert projection.memory["active_window"] is None
    assert projection.memory["conversation_state"] is None
    assert projection.memory["messages"] == [
        {"role": "user", "text": "first", "ts": "2026-01-01T00:00:00+00:00"},
        {"role": "assistant", "text": "second", "ts": "2026-01-02T00:00:00+00:00"},
    ]


def test_projection_reads_empty_rolling_after_clear_without_fallback_to_legacy_lead_field():
    memory_layer = MemoryLayerService(repository=InMemoryMemoryLayerRepository())
    service = ContextProjectionService(leads_repo=_ClearedRollingRepo(), memory_layer=memory_layer)

    projection = asyncio.run(
        service.project(
            lead_id="canonical-42",
            channel="telegram",
            external_user_id="42",
            chat_id="100",
        )
    )

    assert projection.memory["rolling_summary"] is None


def test_projection_ignores_ghost_rolling_document_shape_after_clear():
    memory_layer = MemoryLayerService(repository=InMemoryMemoryLayerRepository())
    service = ContextProjectionService(leads_repo=_GhostRollingRepo(), memory_layer=memory_layer)

    projection = asyncio.run(
        service.project(
            lead_id="canonical-42",
            channel="telegram",
            external_user_id="42",
            chat_id="100",
        )
    )

    assert projection.memory["rolling_summary"] is None


def test_projection_degrades_gracefully_on_partial_read_failures():
    memory_layer = MemoryLayerService(repository=InMemoryMemoryLayerRepository())
    service = ContextProjectionService(leads_repo=_FallbackRepo(), memory_layer=memory_layer)

    projection = asyncio.run(
        service.project(
            lead_id="canonical-42",
            channel="telegram",
            external_user_id="42",
            chat_id=None,
        )
    )

    assert projection.memory["messages"] == []
    assert projection.memory["daily_summary"] is None
    assert projection.memory["rolling_summary"] == "rolling"
    assert projection.memory["active_window"] is None
    assert projection.memory["conversation_state"] is None
