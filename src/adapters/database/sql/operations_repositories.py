"""SQL-backed repositories for queue jobs and worker leases."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select

from src.domain.operations import QueueJobRecord, WorkerLeaseRecord

from .operations_models import QueueJobRow, WorkerLeaseRow
from .operations_serialization import queue_job_from_row, worker_lease_from_row


class SqlOperationsRepository:
    """Persist queue jobs and worker leases in portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""
        self._session_factory = session_factory

    async def get_job_by_idempotency_key(self, *, idempotency_key: str) -> QueueJobRecord | None:
        """Return the durable queue job for the requested idempotency key."""
        async with self._session_factory() as session:
            row = (
                await session.scalars(
                    select(QueueJobRow).where(QueueJobRow.idempotency_key == idempotency_key)
                )
            ).first()
            return None if row is None else queue_job_from_row(row)

    async def enqueue_job(
        self,
        *,
        workflow_type: str,
        workflow_reference: str,
        payload: dict[str, object],
        idempotency_key: str,
        max_attempts: int,
        now,
    ) -> QueueJobRecord:
        """Persist one durable queue job in queued state."""
        row = QueueJobRow(
            queue_job_id=f"queue_job_{int(now.timestamp() * 1000000)}",
            workflow_type=workflow_type,
            workflow_reference=workflow_reference,
            status="queued",
            idempotency_key=idempotency_key,
            payload_json=payload,
            attempt_count=0,
            max_attempts=max_attempts,
            last_error=None,
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
        return queue_job_from_row(row)

    async def get_job(self, *, job_id: str) -> QueueJobRecord | None:
        """Return the durable queue job for the requested identifier."""
        async with self._session_factory() as session:
            row = await session.get(QueueJobRow, job_id)
            return None if row is None else queue_job_from_row(row)

    async def mark_job_processing(self, *, job_id: str, now) -> QueueJobRecord:
        """Mark the requested durable queue job as processing."""
        async with self._session_factory() as session:
            row = await session.get(QueueJobRow, job_id)
            if row is None:
                raise LookupError(f"Unknown queue job: {job_id}")
            row.status = "processing"
            row.attempt_count += 1
            row.updated_at = now
            await session.commit()
            return queue_job_from_row(row)

    async def mark_job_completed(self, *, job_id: str, now) -> QueueJobRecord:
        """Mark the requested durable queue job as completed."""
        async with self._session_factory() as session:
            row = await session.get(QueueJobRow, job_id)
            if row is None:
                raise LookupError(f"Unknown queue job: {job_id}")
            row.status = "completed"
            row.updated_at = now
            await session.commit()
            return queue_job_from_row(row)

    async def mark_job_failed(self, *, job_id: str, error_message: str, now) -> QueueJobRecord:
        """Mark the requested durable queue job as failed."""
        async with self._session_factory() as session:
            row = await session.get(QueueJobRow, job_id)
            if row is None:
                raise LookupError(f"Unknown queue job: {job_id}")
            row.status = "failed"
            row.last_error = error_message
            row.updated_at = now
            await session.commit()
            return queue_job_from_row(row)

    async def acquire_lease(self, *, queue_job_id: str, worker_name: str, now, duration_seconds: int) -> WorkerLeaseRecord:
        """Acquire one durable active worker lease."""
        row = WorkerLeaseRow(
            lease_id=f"lease_{queue_job_id}",
            queue_job_id=queue_job_id,
            worker_name=worker_name,
            status="active",
            acquired_at=now,
            expires_at=now + timedelta(seconds=duration_seconds),
            released_at=None,
        )
        async with self._session_factory() as session:
            existing = await session.get(WorkerLeaseRow, row.lease_id)
            if existing is not None:
                existing.worker_name = worker_name
                existing.status = "active"
                existing.acquired_at = now
                existing.expires_at = now + timedelta(seconds=duration_seconds)
                existing.released_at = None
                await session.commit()
                return worker_lease_from_row(existing)
            session.add(row)
            await session.commit()
        return worker_lease_from_row(row)

    async def renew_lease(self, *, lease_id: str, now, duration_seconds: int) -> WorkerLeaseRecord:
        """Renew one durable active worker lease."""
        async with self._session_factory() as session:
            row = await session.get(WorkerLeaseRow, lease_id)
            if row is None:
                raise LookupError(f"Unknown worker lease: {lease_id}")
            row.expires_at = now + timedelta(seconds=duration_seconds)
            row.status = "active"
            await session.commit()
            return worker_lease_from_row(row)

    async def release_lease(self, *, lease_id: str, now) -> WorkerLeaseRecord:
        """Release one durable active worker lease."""
        async with self._session_factory() as session:
            row = await session.get(WorkerLeaseRow, lease_id)
            if row is None:
                raise LookupError(f"Unknown worker lease: {lease_id}")
            row.status = "released"
            row.released_at = now
            await session.commit()
            return worker_lease_from_row(row)

    async def count_jobs_by_status(self, *, status: str) -> int:
        """Return the number of durable queue jobs in the requested status."""
        async with self._session_factory() as session:
            result = await session.scalar(
                select(func.count()).select_from(QueueJobRow).where(QueueJobRow.status == status)
            )
            return int(result or 0)
