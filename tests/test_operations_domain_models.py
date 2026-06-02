from __future__ import annotations

from datetime import datetime, timezone

from src.domain.operations import QueueJobRecord, QueueJobStatus, WorkerLeaseRecord, WorkerLeaseStatus


def test_queue_job_record_keeps_workflow_kind_and_idempotency_key() -> None:
    job = QueueJobRecord(
        job_id="queue_job_1",
        workflow_type="try_on",
        workflow_reference="try_on_123",
        status=QueueJobStatus.QUEUED,
        idempotency_key="try_on:try_on_123",
    )

    assert job.workflow_type == "try_on"
    assert job.idempotency_key == "try_on:try_on_123"


def test_worker_lease_record_tracks_owner_and_expiry() -> None:
    lease = WorkerLeaseRecord(
        lease_id="lease_1",
        queue_job_id="queue_job_1",
        worker_name="portable-worker",
        status=WorkerLeaseStatus.ACTIVE,
        acquired_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )

    assert lease.worker_name == "portable-worker"
