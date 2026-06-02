from __future__ import annotations

from fastapi.testclient import TestClient
from types import SimpleNamespace

from src.main import app

client = TestClient(app)


def test_health_route_reports_queue_and_worker_readiness(monkeypatch) -> None:
    from src.entrypoints import status_routes
    app.state.settings = SimpleNamespace(
        public_status_endpoints_enabled=False,
        status_endpoint_token="test-token",
        postgres_dsn=None,
        redis_url=None,
        object_storage_backend="in_memory",
        qdrant_url=None,
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
