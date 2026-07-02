from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.operations_repositories import SqlOperationsRepository


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_operations_repository_enqueues_and_reads_queue_job() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlOperationsRepository(session_factory=session_factory)

    job = await repository.enqueue_job(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
        max_attempts=3,
        now=_utc_now(),
    )
    saved = await repository.get_job(job_id=job.job_id)

    assert saved is not None
    assert saved.status.value == "queued"
    await engine.dispose()


@pytest.mark.asyncio
async def test_operations_repository_claims_and_releases_worker_lease() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlOperationsRepository(session_factory=session_factory)

    job = await repository.enqueue_job(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
        max_attempts=3,
        now=_utc_now(),
    )
    lease = await repository.acquire_lease(
        queue_job_id=job.job_id,
        worker_name="portable-worker",
        now=_utc_now(),
        duration_seconds=300,
    )
    released = await repository.release_lease(lease_id=lease.lease_id, now=_utc_now())

    assert released.status.value == "released"
    await engine.dispose()


@pytest.mark.asyncio
async def test_operations_repository_claims_stale_processing_job() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlOperationsRepository(session_factory=session_factory)
    now = _utc_now()

    job = await repository.enqueue_job(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
        max_attempts=3,
        now=now - timedelta(minutes=10),
    )
    await repository.mark_job_processing(job_id=job.job_id, now=now - timedelta(minutes=10))

    reclaimed = await repository.claim_stale_processing_job(
        stale_before=now - timedelta(minutes=5),
        now=now,
    )

    assert reclaimed is not None
    assert reclaimed.job_id == job.job_id
    assert reclaimed.status.value == "queued"
    await engine.dispose()
