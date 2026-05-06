from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from src.memory_layer.run_ledger_repository import InMemoryMemoryRunLedgerRepository
from src.memory_layer.services.memory_run_ledger_service import MemoryRunLedgerService
from src.memory_layer.services.memory_sync_persistence_service import MemorySyncPersistenceService
from src.memory_layer.services.memory_sync_port import MemorySyncPort
from src.runtime_agents.memory_agent.contracts import DailyMemoryContract
from src.memory_layer.use_cases import ApplyDailyAgentOutputUseCase
from src.memory_layer.use_cases.process_daily_agent_output_use_case import ProcessDailyAgentOutputUseCase
from src.services.crm.crm_memory_sync_service import CrmMemorySyncResult
from src.services.runtime.feature_flags import FeatureFlags


class _ProfileSpy:
    def __init__(self, *, validate_ok: bool = True, semantic_ok: bool = True) -> None:
        self.calls: list[str] = []
        self.validate_ok = validate_ok
        self.semantic_ok = semantic_ok

    def parse(self, raw_payload: DailyMemoryContract):
        self.calls.append("parse")
        return type("_Typed", (), {"memory_payload": raw_payload})()

    def validate(self, typed_output):
        _ = typed_output
        self.calls.append("validate")
        return type("_Val", (), {"ok": self.validate_ok})()

    def semantic_validate(self, typed_output, context):
        _ = (typed_output, context)
        self.calls.append("semantic_validate")
        return type("_Sem", (), {"ok": self.semantic_ok})()


class _RegistryStub:
    def __init__(self, profile):
        self.profile = profile

    def get_profile(self, *, flow: str):
        assert flow == "memory"
        return self.profile


def _memory_run_ledger_service() -> MemoryRunLedgerService:
    return MemoryRunLedgerService(repository=InMemoryMemoryRunLedgerRepository())


class _CrmSyncStub:
    async def sync_memory(self, **_kwargs):
        return CrmMemorySyncResult(ok=False, reason_code="crm_sync_disabled")


def test_memory_process_use_case_runs_profile_pipeline_in_order():
    profile = _ProfileSpy()
    use_case = ProcessDailyAgentOutputUseCase(profile_registry=_RegistryStub(profile))

    payload = DailyMemoryContract.model_validate({"daily_summary": {"summary_text": "daily", "open_questions": [], "carry_forward_notes": [], "learned_facts": [], "changed_facts": [], "memory_relevance_flags": []}})
    result = use_case.execute(payload=payload)

    assert profile.calls == ["parse", "validate", "semantic_validate"]
    assert result.accepted is True


def test_memory_process_use_case_blocks_on_profile_semantic_reject():
    profile = _ProfileSpy(semantic_ok=False)
    use_case = ProcessDailyAgentOutputUseCase(profile_registry=_RegistryStub(profile))

    payload = DailyMemoryContract.model_validate({"daily_summary": {"summary_text": "daily", "open_questions": [], "carry_forward_notes": [], "learned_facts": [], "changed_facts": [], "memory_relevance_flags": []}})
    result = use_case.execute(payload=payload)

    assert result.accepted is False
    assert result.error_code == "domain_semantic_invalid"
