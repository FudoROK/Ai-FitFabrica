from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.identity_audit import (
    SqlIdentityResolutionAuditRecorder,
    build_identity_resolution_audit_entry,
)
from src.adapters.database.sql.identity_repositories import SqlChannelIdentityRepository
from src.adapters.database.sql.identity_repositories import SqlIdentityBindingRepository, SqlLeadRepository
from src.adapters.database.sql.identity_models import IdentityResolutionAuditRow
from src.identity_core.models.identity_binding import IdentityBindingRecord
from src.identity_core.models.identity_core_primitives import IdentityBindingState, LeadLifecycleState
from src.identity_core.models.lead import LeadRecord
from src.identity_core.services.identity_resolution import RuntimeIdentityResolutionResult


def test_sql_channel_identity_repository_reports_component_name() -> None:
    repository = SqlChannelIdentityRepository(session_factory=None)

    assert repository.__class__.__name__ == "SqlChannelIdentityRepository"


def test_identity_resolution_result_exposes_binding_created_flag() -> None:
    result = RuntimeIdentityResolutionResult(
        canonical_lead_id="lead-1",
        channel_identity_id="channel-1",
        channel="telegram",
        external_identity="42",
        binding_created=True,
    )

    assert result.binding_created is True


@pytest.mark.asyncio
async def test_sql_repositories_persist_identity_resolution_flow() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    channel_repo = SqlChannelIdentityRepository(session_factory=session_factory)
    lead_repo = SqlLeadRepository(session_factory=session_factory)
    binding_repo = SqlIdentityBindingRepository(session_factory=session_factory)

    channel_identity = await channel_repo.get_or_create_channel_identity(
        channel="telegram",
        external_identity="42",
        metadata={"source": "test"},
    )
    lead = await lead_repo.create_lead(
        lead=LeadRecord(
            lead_id=uuid4(),
            person_id=channel_identity.person_id,
            lifecycle_state=LeadLifecycleState.ACTIVE,
            display_name=None,
            metadata={"first_channel": "telegram", "first_external_identity": "42"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    binding = await binding_repo.create_binding(
        binding=IdentityBindingRecord(
            identity_binding_id=uuid4(),
            channel_identity_id=channel_identity.channel_identity_id,
            lead_id=lead.lead_id,
            binding_state=IdentityBindingState.ACTIVE,
            decision_basis="test",
            provenance={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    resolved_lead = await lead_repo.lookup_lead_by_channel_identity(channel="telegram", external_identity="42")
    active_binding = await binding_repo.get_active_binding_for_channel_identity(
        channel_identity_id=channel_identity.channel_identity_id
    )

    assert resolved_lead is not None
    assert resolved_lead.person_id == channel_identity.person_id
    assert active_binding is not None
    assert active_binding.identity_binding_id == binding.identity_binding_id

    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_binding_repository_revocation_removes_active_binding() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    channel_repo = SqlChannelIdentityRepository(session_factory=session_factory)
    lead_repo = SqlLeadRepository(session_factory=session_factory)
    binding_repo = SqlIdentityBindingRepository(session_factory=session_factory)

    channel_identity = await channel_repo.get_or_create_channel_identity(channel="telegram", external_identity="99")
    lead = await lead_repo.create_lead(
        lead=LeadRecord(
            lead_id=uuid4(),
            person_id=channel_identity.person_id,
            lifecycle_state=LeadLifecycleState.ACTIVE,
            display_name=None,
            metadata={"first_channel": "telegram", "first_external_identity": "99"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    binding = await binding_repo.create_binding(
        binding=IdentityBindingRecord(
            identity_binding_id=uuid4(),
            channel_identity_id=channel_identity.channel_identity_id,
            lead_id=lead.lead_id,
            binding_state=IdentityBindingState.ACTIVE,
            decision_basis="test",
            provenance={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    await binding_repo.revoke_binding(identity_binding_id=binding.identity_binding_id, reason="duplicate")
    active_binding = await binding_repo.get_active_binding_for_channel_identity(
        channel_identity_id=channel_identity.channel_identity_id
    )

    assert active_binding is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_identity_audit_recorder_persists_resolution_entry() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    channel_repo = SqlChannelIdentityRepository(session_factory=session_factory)
    lead_repo = SqlLeadRepository(session_factory=session_factory)
    recorder = SqlIdentityResolutionAuditRecorder(session_factory=session_factory)

    channel_identity = await channel_repo.get_or_create_channel_identity(channel="telegram", external_identity="77")
    lead = await lead_repo.create_lead(
        lead=LeadRecord(
            lead_id=uuid4(),
            person_id=channel_identity.person_id,
            lifecycle_state=LeadLifecycleState.ACTIVE,
            display_name=None,
            metadata={"first_channel": "telegram", "first_external_identity": "77"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    entry = build_identity_resolution_audit_entry(
        result=RuntimeIdentityResolutionResult(
            canonical_lead_id=str(lead.lead_id),
            channel_identity_id=str(channel_identity.channel_identity_id),
            channel="telegram",
            external_identity="77",
            binding_created=True,
            person_created=False,
            lead_created=True,
        ),
        external_identity_hash="abc123",
        lead_id=lead.lead_id,
        person_id=channel_identity.person_id,
        channel_identity_id=channel_identity.channel_identity_id,
        decision_mode="runtime:auto_create_on_first_contact",
    )

    await recorder.record(entry=entry)

    async with session_factory() as session:
        rows = (await session.scalars(select(IdentityResolutionAuditRow))).all()

    assert len(rows) == 1
    assert rows[0].lead_id == lead.lead_id
    assert rows[0].channel_identity_id == channel_identity.channel_identity_id

    await engine.dispose()
