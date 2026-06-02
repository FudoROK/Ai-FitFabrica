from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.billing_repositories import SqlBillingRepository
from src.domain.billing import BillingEventType, BillingOwnerType, LedgerAppendRequest


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_billing_repository_creates_account_and_appends_ledger_event() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlBillingRepository(session_factory=session_factory)

    account = await repository.ensure_account(owner_id="user-1", owner_type="person", initial_credits=100)
    event = await repository.append_ledger_event(
        LedgerAppendRequest(
            owner_id="user-1",
            owner_type=BillingOwnerType.PERSON,
            event_type=BillingEventType.CHARGE,
            credits_delta=-12,
            workflow_type="try_on",
            workflow_reference="job-1",
            stage_name="completed",
            idempotency_key="person:user-1:try_on:job-1:completed",
            created_at=_utc_now(),
        )
    )

    assert account.owner_id == "user-1"
    assert event.balance_after_event == 88
    await engine.dispose()


@pytest.mark.asyncio
async def test_billing_repository_is_idempotent_for_duplicate_event_key() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlBillingRepository(session_factory=session_factory)
    await repository.ensure_account(owner_id="user-1", owner_type="person", initial_credits=100)

    request = LedgerAppendRequest(
        owner_id="user-1",
        owner_type=BillingOwnerType.PERSON,
        event_type=BillingEventType.CHARGE,
        credits_delta=-12,
        workflow_type="try_on",
        workflow_reference="job-1",
        stage_name="completed",
        idempotency_key="person:user-1:try_on:job-1:completed",
        created_at=_utc_now(),
    )
    first = await repository.append_ledger_event(request)
    second = await repository.append_ledger_event(request)

    assert first.event_id == second.event_id
    await engine.dispose()
