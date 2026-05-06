from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract
from src.runtime_agents.memory_agent.contracts.rolling import RollingMemoryContract
from src.memory_layer.domain import MemoryRunResult
from src.memory_layer.run_ledger_repository import InMemoryMemoryRunLedgerRepository
from src.memory_layer.services.memory_run_ledger_service import MemoryRunLedgerService
from src.memory_layer.services.memory_sync_persistence_service import LeadMemoryContext
from src.memory_layer.services.memory_sync_port import MemorySyncPort
from src.services.runtime.feature_flags import FeatureFlags


@dataclass(frozen=True)
class _PrepResult:
    output: object | None
    error_code: str | None = None


class _MemorySummaryServiceStub:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def generate_memory_output(self, **_kwargs):
        self.calls.append("generate_daily")
        payload = DailyMemoryContract.model_validate(
            {
                "daily_summary": {
                    "summary_text": "daily",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                }
            }
        )
        return _PrepResult(output=payload)

    async def generate_rolling_update(self, **_kwargs):
        self.calls.append("generate_rolling")
        payload = RollingMemoryContract.model_validate(
            {
                "rolling_update": {
                    "rolling_summary_text": "rolling",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "days_count": 1,
                    "last_daily_summary_date": "2026-01-01",
                    "version": 1,
                }
            }
        )
        return _PrepResult(output=payload)


class _PersistenceStub:
    def __init__(self) -> None:
        pass

    async def load_lead_context(self, *, lead_id: str, include_rolling: bool = True) -> LeadMemoryContext:
        _ = (lead_id, include_rolling)
        return LeadMemoryContext(
            lead_data={"channel_user_id": "42"},
            lead_profile={"first_name": "Ann"},
            rolling_summary="rolling-prev",
            rolling_payload={"rolling_summary_text": "rolling-prev", "version": 1, "rolling_hash": "h1"},
            active_window={"local_day_key": "2026-01-01"},
            conversation_state={},
        )

    async def fetch_messages(self, *, lead_id: str, start_utc: datetime, end_utc: datetime):
        _ = (lead_id, start_utc, end_utc)
        return [{"role": "user", "text": "hi"}]

    async def fetch_confirmed_rolling_summary_validation(self, *, lead_id: str):
        _ = lead_id
        return type(
            "_Confirmed",
            (),
            {"ok": True, "reason_code": None, "normalized_text": "rolling", "rolling_version": 1, "rolling_hash": "h1"},
        )()

class _DailyProcessUseCaseStub:
    def execute(self, *, payload, correlation_id=None):
        _ = correlation_id
        return type("_Res", (), {"accepted": True, "output": payload, "error_code": None})()


class _RollingProcessUseCaseStub:
    def execute(self, *, payload, correlation_id=None):
        _ = correlation_id
        return type("_Res", (), {"accepted": True, "output": payload, "error_code": None})()


class _ApplyDailyUseCaseStub:
    def __init__(self, *, write_status: str = "applied") -> None:
        self.write_status = write_status
        self.calls = 0

    async def execute(self, **_kwargs):
        self.calls += 1
        return type(
            "_DailyApply",
            (),
            {
                "daily_summary_text": "daily",
                "daily_summary_payload": {"summary_text": "daily"},
                "daily_written": self.write_status == "applied",
                "write_status": self.write_status,
                "write_error_code": None if self.write_status == "applied" else "daily_payload_conflict",
            },
        )()


class _ApplyRollingUseCaseStub:
    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, **_kwargs):
        self.calls += 1
        return type(
            "_RollingApply",
            (),
            {
                "rolling_summary_text": "rolling",
                "rolling_update_payload": {"rolling_summary_text": "rolling"},
                "rolling_written": True,
                "write_status": "applied",
                "write_error_code": None,
            },
        )()


class _RepoStub:
    pass


def _build_port(*, daily_write_status: str = "applied"):
    memory_service = _MemorySummaryServiceStub()
    persistence = _PersistenceStub()
    apply_daily = _ApplyDailyUseCaseStub(write_status=daily_write_status)
    apply_rolling = _ApplyRollingUseCaseStub()
    port = MemorySyncPort(
        leads_repo=_RepoStub(),
        memory_summary_service=memory_service,
        persistence_service=persistence,
        crm_memory_sync_service=None,
        process_daily_agent_output_use_case=_DailyProcessUseCaseStub(),
        apply_daily_agent_output_use_case=apply_daily,
        process_rolling_agent_output_use_case=_RollingProcessUseCaseStub(),
        apply_rolling_agent_output_use_case=apply_rolling,
        memory_run_ledger_service=MemoryRunLedgerService(repository=InMemoryMemoryRunLedgerRepository()),
        feature_flags=FeatureFlags(enable_profile_runtime=True, enable_memory_profile=True),
    )
    return port, memory_service, persistence, apply_daily, apply_rolling


def _run(port: MemorySyncPort) -> MemoryRunResult:
    return asyncio.run(
        port.process_lead_daily_summary(
            lead_id="lead-1",
            start_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
            memory_day_key="2026-01-01",
            errors=[],
        )
    )


def test_split_sequence_daily_then_rolling_after_daily_persist():
    port, memory_service, _persistence, apply_daily, apply_rolling = _build_port(daily_write_status="applied")

    result = _run(port)

    assert result.outcome == "success"
    assert apply_daily.calls == 1
    assert apply_rolling.calls == 1
    assert memory_service.calls == ["generate_daily", "generate_rolling"]
    stages = [item.stage for item in result.stage_details]
    assert stages.index("daily_apply") < stages.index("rolling_prepare")
    assert stages.index("rolling_prepare") < stages.index("rolling_apply")


def test_split_sequence_skips_rolling_when_daily_persist_fails():
    port, memory_service, _persistence, apply_daily, apply_rolling = _build_port(daily_write_status="conflict")

    result = _run(port)

    assert result.outcome == "failed"
    assert apply_daily.calls == 1
    assert apply_rolling.calls == 0
    assert memory_service.calls == ["generate_daily"]
    stages = [item.stage for item in result.stage_details]
    assert "rolling_prepare" not in stages
