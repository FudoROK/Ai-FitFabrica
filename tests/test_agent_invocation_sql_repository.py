from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.agent_invocation_models import AgentInvocationRow
from src.adapters.database.sql.agent_invocation_repositories import SqlAgentInvocationRepository
from src.adapters.database.sql.base import SqlBase
from src.domain.agent_runtime import AgentInvocationRecord, AgentRuntimeStatus, AgentValidationStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_agent_invocation_repository_persists_audit_metadata_without_raw_payloads() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlAgentInvocationRepository(session_factory=session_factory)
    now = _utc_now()
    record = AgentInvocationRecord(
        invocation_id="invocation-1",
        trace_id="trace-1",
        agent_name="human_identity_agent",
        prompt_version="human_identity.v1",
        contract_version="human_identity.contract.v1",
        provider="vertex",
        model="gemini-2.5-flash",
        status=AgentRuntimeStatus.SUCCEEDED,
        validation_status=AgentValidationStatus.PASSED,
        latency_ms=42,
        confidence=0.91,
        cost_metadata={"input_tokens": 120},
        input_fields=["human_photo_object_key"],
        output_fields=["confidence", "summary"],
        started_at=now,
        completed_at=now,
    )

    await repository.save(record)
    saved = await repository.get(invocation_id="invocation-1")

    assert saved == record
    assert AgentInvocationRow.__tablename__ == "agent_invocations"
    assert "input_payload" not in AgentInvocationRow.__table__.columns
    assert "output_payload" not in AgentInvocationRow.__table__.columns
    assert "prompt" not in AgentInvocationRow.__table__.columns
    await engine.dispose()

