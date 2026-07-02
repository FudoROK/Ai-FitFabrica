from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.entrypoints import runtime_dependencies as deps


def _settings(environment: str = "prod"):
    return SimpleNamespace(
        environment=environment,
        ingress_rate_limit_max_events=20,
        ingress_rate_limit_window_seconds=60,
        ingress_rate_limit_collection="ingress_rate_limits",
        ingress_global_safety_cap_max_events=2000,
        object_storage_prefix="fitfabrica",
        operations_queue_backend="in_memory",
        operations_queue_name="fitfabrica:workflow-queue",
        operations_worker_name="portable-worker",
        processing_lease_duration_seconds=300,
        postgres_dsn=None,
        redis_url=None,
    )


def test_operations_runtime_dependencies_select_portable_queue_backend(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, redis_client=None, object_storage=object()),
    )

    runtime = deps.operations_runtime_dependencies(settings)

    assert runtime.dispatch_service is not None
    assert runtime.worker_runtime is not None
    assert "business_catalog_search_index" in runtime.worker_runtime._handlers


def test_operations_runtime_dependencies_are_cached(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, redis_client=None, object_storage=object()),
    )

    first = deps.operations_runtime_dependencies(settings)
    second = deps.operations_runtime_dependencies(settings)

    assert first is second


@pytest.mark.asyncio
async def test_operations_worker_runs_business_catalog_search_index_job(monkeypatch) -> None:
    settings = _settings()
    called_product_ids: list[list[str]] = []

    class _Workflow:
        async def index_product_ids(self, *, product_ids: list[str]):
            called_product_ids.append(product_ids)
            return None

    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, redis_client=None, object_storage=object()),
    )
    monkeypatch.setattr(
        deps,
        "business_catalog_search_indexing_runtime_dependencies",
        lambda _settings: SimpleNamespace(workflow_service=_Workflow()),
    )

    runtime = deps.operations_runtime_dependencies(settings)
    await runtime.dispatch_service.enqueue_workflow(
        workflow_type="business_catalog_search_index",
        workflow_reference="product_1",
        payload={"product_ids": ["product_1"]},
        idempotency_key="business_catalog_search_index:product_1:test",
    )

    result = await runtime.worker_runtime.run_one_cycle()

    assert result.completed_jobs == 1
    assert called_product_ids == [["product_1"]]
