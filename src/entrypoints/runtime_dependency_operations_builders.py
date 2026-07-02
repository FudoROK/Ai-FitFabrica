"""Operations runtime builders extracted from workflow wiring."""
from __future__ import annotations

from src.adapters.database.sql.operations_repositories import SqlOperationsRepository
from src.adapters.operations import InMemoryOperationsRepository
from src.adapters.queue import InMemoryQueue, RedisQueue
from src.entrypoints.runtime_dependency_contracts import OperationsRuntimeDependencies
from src.entrypoints.runtime_dependency_foundation_builders import utc_now
from src.use_cases.operations import OperationsHealthService, WorkerLeaseService, WorkflowDispatchService
from src.services.workers.worker_runtime import WorkerRuntime


def build_operations_runtime_dependencies(
    settings,
    *,
    infrastructure,
    try_on_runtime,
    product_card_runtime,
    content_package_runtime,
    pricing_runtime,
    business_catalog_search_index_runtime,
) -> OperationsRuntimeDependencies:
    """Build the operations runtime bundle for the current settings instance."""

    repository = (
        SqlOperationsRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryOperationsRepository()
    )
    queue_backend = getattr(settings, "operations_queue_backend", "in_memory")
    if queue_backend == "redis" and getattr(infrastructure, "redis_client", None) is not None:
        queue = RedisQueue(
            redis_client=infrastructure.redis_client,
            queue_name=getattr(settings, "operations_queue_name", "fitfabrica:workflow-queue"),
        )
        resolved_backend = "redis"
    else:
        queue = InMemoryQueue()
        resolved_backend = "in_memory"
    lease_service = WorkerLeaseService(
        repository=repository,
        clock=utc_now,
        lease_duration_seconds=getattr(settings, "processing_lease_duration_seconds", 300),
    )
    worker_name = getattr(settings, "operations_worker_name", "portable-worker")
    handlers = {
        "try_on": lambda job: try_on_runtime().workflow_service.execute_job(
            job_id=job.workflow_reference,
            lifecycle_mode=job.payload.get("sandbox_lifecycle_mode", "complete"),
        ),
        "product_card": lambda job: product_card_runtime().workflow_service.execute_product_card_job(job_id=job.workflow_reference),
        "content_package": lambda job: content_package_runtime().workflow_service.execute_content_package_job(job_id=job.workflow_reference),
        "pricing": lambda job: pricing_runtime().workflow_service.execute_pricing_job(job_id=job.workflow_reference),
        "business_catalog_search_index": lambda job: business_catalog_search_index_runtime().workflow_service.index_product_ids(
            product_ids=_product_ids_from_payload(job.payload),
        ),
    }
    return OperationsRuntimeDependencies(
        dispatch_service=WorkflowDispatchService(repository=repository, queue=queue, clock=utc_now),
        worker_runtime=WorkerRuntime(
            queue=queue,
            repository=repository,
            lease_service=lease_service,
            handlers=handlers,
            worker_name=worker_name,
            clock=utc_now,
            stale_reclaim_seconds=getattr(settings, "processing_stale_reclaim_seconds", 300),
        ),
        health_service=OperationsHealthService(
            repository=repository,
            queue_backend=resolved_backend,
            worker_name=worker_name,
            postgres_configured=bool(getattr(settings, "postgres_dsn", None)),
            redis_configured=bool(getattr(settings, "redis_url", None)),
        ),
    )


def _product_ids_from_payload(payload: dict[str, object]) -> list[str]:
    """Extract business catalog product ids from a queue job payload."""

    raw_product_ids = payload.get("product_ids")
    if not isinstance(raw_product_ids, list):
        return []
    return [product_id for product_id in raw_product_ids if isinstance(product_id, str) and product_id.strip()]
