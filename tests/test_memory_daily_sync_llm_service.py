from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from types import SimpleNamespace

import pytest
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from src.runtime_agents.memory_agent.contracts import DailyMemoryContract
from src.services.runtime.feature_flags import FeatureFlags
from src.memory_layer.run_ledger_repository import InMemoryMemoryRunLedgerRepository
from src.memory_layer.services.memory_run_ledger_service import MemoryRunLedgerService
from src.memory_layer.services.memory_sync_llm_service import MemoryOutputExtractionResult, MemorySummaryService
from src.memory_layer.services.memory_sync_persistence_service import LeadMemoryContext
from src.memory_layer.services.memory_sync_port import MemorySyncPort


class _LLMResult:
    def __init__(self, *, ok: bool, data=None, error=None, provider_metadata=None):
        self.ok = ok
        self.data = data
        self.error = error
        self.provider_metadata = provider_metadata


class _TrackingLLMService:
    def __init__(self, result: _LLMResult):
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    async def run(self, *, task, payload, meta):
        self.calls.append((task, payload))
        return self.result


class _RoutingLLMService:
    def __init__(self, responses: dict[str, _LLMResult]):
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    async def run(self, *, task, payload, meta):
        self.calls.append((task, payload))
        return self.responses[task]


class _FirestoreTimestampStub:
    def __init__(self, dt: datetime):
        self._dt = dt

    def to_datetime(self) -> datetime:
        return self._dt


def _canonical_rolling_update(
    summary_text: str = "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.",
) -> dict[str, object]:
    return {
        "rolling_summary_text": summary_text,
        "open_questions": [],
        "carry_forward_notes": [],
        "days_count": 1,
        "last_daily_summary_date": "2025-01-01",
        "version": 1,
    }


def _memory_run_ledger_service() -> MemoryRunLedgerService:
    return MemoryRunLedgerService(repository=InMemoryMemoryRunLedgerRepository())


@pytest.mark.asyncio
async def test_memory_sync_llm_service_uses_llm_service_only():
    llm_service = _TrackingLLMService(
        _LLMResult(
            ok=True,
            data={
                "daily_summary": {"summary_text": "daily from structured"},
            },
        )
    )
    service = MemorySummaryService(llm_service=llm_service)

    result = await service.generate_memory_output(
        lead_id="lead-1",
        lead_profile={"first_name": "Ann"},
        active_window={"local_day_key": "2025-01-01"},
        conversation_state={"current_stage": "qualification"},
        messages=[{"role": "user", "text": "hello"}],
    )

    assert result.output is not None
    assert result.error_code is None
    assert result.output.daily_summary.summary_text == "daily from structured"
    assert llm_service.calls and llm_service.calls[0][0] == "memory_daily_sync_task"
    assert len(llm_service.calls) == 1
    assert not hasattr(service, "vertex_memory_provider")
    assert not hasattr(service, "memory_agent_resource")


@pytest.mark.asyncio
async def test_memory_sync_llm_service_uses_memory_runtime_task_when_flag_enabled():
    llm_service = _RoutingLLMService(
        {
            "memory_daily_sync_task": _LLMResult(
                ok=True,
                data={
                    "active_window_update": None,
                    "daily_summary": {"summary_text": "daily from memory_sync"},
                    "conversation_state_update": None,
                },
            ),
            "daily_summary": _LLMResult(ok=False, error={"kind": "UNUSED"}),
        }
    )
    service = MemorySummaryService(
        llm_service=llm_service,
        settings=SimpleNamespace(),
    )

    result = await service.generate_memory_output(
        lead_id="lead-1",
        lead_profile={"first_name": "Ann"},
        active_window={"local_day_key": "2025-01-01"},
        conversation_state={"current_stage": "qualification"},
        messages=[{"role": "user", "text": "hello"}],
    )

    assert result.output is not None
    assert result.output.daily_summary.summary_text == "daily from memory_sync"
    assert [call[0] for call in llm_service.calls] == ["memory_daily_sync_task"]
