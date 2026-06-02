from __future__ import annotations

from src.adapters.database.sql.operations_models import QueueJobRow, WorkerLeaseRow


def test_operations_sql_models_define_queue_and_lease_tables() -> None:
    assert QueueJobRow.__tablename__ == "workflow_queue_jobs"
    assert WorkerLeaseRow.__tablename__ == "worker_leases"
