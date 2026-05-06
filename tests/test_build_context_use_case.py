from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from src.memory_layer import InMemoryMemoryLayerRepository, MemoryLayerService
from src.services.context.core_context_builder import build_core_context


class _Lead:
    rolling_summary = "rolling"

    def model_dump(self, mode: str = "python") -> dict:
        assert mode == "python"
        return {"lead_state": "warm"}


class _Repo:
    async def get(self, lead_id: str):
        assert lead_id == "canonical-123"
        return _Lead()

    async def fetch_last_messages(self, *, lead_id: str, since, limit: int = 30):
        assert lead_id == "canonical-123"
        return [
            {"role": "assistant", "text": "canonical first", "timestamp": datetime(2026, 2, 1, tzinfo=timezone.utc)},
            {"role": "user", "text": "canonical message", "timestamp": datetime(2026, 2, 2, tzinfo=timezone.utc)},
        ]

    async def fetch_latest_daily_summary(self, *, lead_id: str):
        return {"summary_text": "daily"}

    async def fetch_rolling_summary(self, *, lead_id: str):
        return {"rolling_summary_text": "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.", "days_count": 1, "version": 1, "last_daily_summary_date": "2026-02-01"}


def test_build_context_payload_keeps_runtime_payload_contract():
    payload = asyncio.run(
        build_core_context(
            lead_id="canonical-123",
            channel="telegram",
            external_user_id="123",
            chat_id="456",
            leads_repo=_Repo(),
            memory_layer=MemoryLayerService(repository=InMemoryMemoryLayerRepository()),
        )
    )

    assert payload == {
        "identity": {
            "channel": "telegram",
            "external_user_id": "123",
            "chat_id": "456",
            "lead_id": "canonical-123",
        },
        "lead_snapshot": {"lead_state": "warm"},
        "memory": {
            "rolling_summary": "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.",
            "daily_summary": "daily",
            "last_messages": [
                {"role": "assistant", "text": "canonical first", "ts": "2026-02-01T00:00:00+00:00"},
                {"role": "user", "text": "canonical message", "ts": "2026-02-02T00:00:00+00:00"},
            ],
        },
    }
