from __future__ import annotations

from fastapi.testclient import TestClient
from types import SimpleNamespace

from src.main import app

client = TestClient(app)


def test_health_route_reports_queue_and_worker_readiness(monkeypatch) -> None:
    from src.entrypoints import status_routes
    monkeypatch.setattr(
        app.state,
        "settings",
        SimpleNamespace(
            environment="test",
            public_status_endpoints_enabled=False,
            status_endpoint_token="test-token",
            postgres_dsn=None,
            redis_url=None,
            object_storage_backend="in_memory",
            qdrant_url=None,
        ),
    )

    class _HealthStub:
        async def snapshot(self):
            return type(
                "Snapshot",
                (),
                {
                    "model_dump": lambda self, mode="json": {
                        "queue_backend": "in_memory",
                        "queue_depth": 0,
                        "worker_name": "portable-worker",
                        "redis_status": "not_configured",
                        "postgres_status": "not_configured",
                    }
                },
            )()

    monkeypatch.setattr(
        status_routes,
        "operations_runtime_dependencies",
        lambda settings: type("Runtime", (), {"health_service": _HealthStub()})(),
    )

    response = client.get("/health", headers={"X-Status-Token": "test-token"})

    assert response.status_code == 200
    assert "operations" in response.json()
    assert "try_on_real_activation" in response.json()


def test_ready_route_reports_no_billing_blockers_without_provider_side_effects(monkeypatch) -> None:
    monkeypatch.setattr(
        app.state,
        "settings",
        SimpleNamespace(
            environment="test",
            public_status_endpoints_enabled=False,
            status_endpoint_token="test-token",
            postgres_dsn="postgresql+asyncpg://fitfabrica:test@localhost:5432/fitfabrica",
            redis_url=None,
            object_storage_backend="in_memory",
            object_storage_bucket_name=None,
            qdrant_url=None,
            billing_core_enabled=False,
            admin_api_token=None,
            allow_unsafe_admin_header_auth=False,
            enable_admin_business_catalog=True,
            enable_admin_taxonomy=True,
            enable_admin_costs=True,
            enable_search_engine_discovery=True,
            search_engine_discovery_provider="google_programmable_search",
            search_engine_discovery_api_key=None,
            search_engine_discovery_daily_limit=25,
            llm_provider="vertex",
            llm_gateway_mode="stub",
            vertex_project=None,
            image_editing_provider="stub",
            try_on_generation_backend="sandbox_fake",
            enable_real_try_on_generation=False,
            operations_queue_backend="in_memory",
        ),
    )

    response = client.get("/ready", headers={"X-Status-Token": "test-token"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["mode"] == "no_billing_preparation"
    assert payload["services"]["sql"]["status"] == "configured"
    assert payload["services"]["billing"]["status"] == "blocked"
    assert payload["services"]["auth"]["status"] == "blocked"
    assert payload["services"]["search_engine_discovery"]["status"] == "blocked"
    assert "billing_core_not_enabled" in payload["blockers"]
    assert "admin_auth_not_configured" in payload["blockers"]
    assert "public_demo_request_capture" in payload["safe_without_billing"]
    assert "restore_billing_provider_and_credit_ledger_gate" in payload["post_billing_checks"]
