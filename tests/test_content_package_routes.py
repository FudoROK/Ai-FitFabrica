from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app
from src.domain.content_package import ContentPackageJobRecord

client = TestClient(app)


class _DispatchStub:
    async def enqueue_workflow(self, **kwargs):
        return None


class _WorkerStub:
    async def run_one_cycle(self):
        return None


class _ServiceStub:
    async def create_content_package_job(self, *, request):
        return ContentPackageJobRecord(
            job_id="content_package_123",
            product_card_version_id=request.product_card_version_id,
            package_name=request.package_name,
            status="accepted",
            requested_channels=list(request.requested_channels),
            created_at="2026-05-31T00:00:00+00:00",
            updated_at="2026-05-31T00:00:00+00:00",
        )

    async def get_job(self, job_id: str):
        return {
            "job_id": job_id,
            "product_card_version_id": "product_card_123_v1",
            "package_name": "marketplace-launch",
            "status": "completed",
            "requested_channels": ["wildberries", "instagram"],
            "created_at": "2026-05-31T00:00:00+00:00",
            "updated_at": "2026-05-31T00:00:00+00:00",
        }

    async def get_result(self, job_id: str):
        return {
            "version_id": f"{job_id}_v1",
            "job_id": job_id,
            "package_name": "marketplace-launch",
            "assets": [
                {"asset_kind": "caption", "label": "Instagram caption"},
                {"asset_kind": "listing", "label": "Marketplace listing"},
            ],
            "created_at": "2026-05-31T00:00:00+00:00",
        }


def test_content_package_route_returns_structured_response(monkeypatch) -> None:
    from src.entrypoints import content_package_routes
    runtime = type("WorkflowRuntime", (), {"workflow_service": _ServiceStub()})()
    ops_runtime = type("OpsRuntime", (), {"dispatch_service": _DispatchStub(), "worker_runtime": _WorkerStub()})()

    monkeypatch.setattr(
        content_package_routes,
        "content_package_runtime_dependencies",
        lambda settings: runtime,
    )
    monkeypatch.setattr(content_package_routes, "operations_runtime_dependencies", lambda settings: ops_runtime)

    response = client.post(
        "/api/content-packages",
        json={
            "product_card_version_id": "product_card_123_v1",
            "package_name": "marketplace-launch",
            "requested_channels": ["wildberries", "instagram"],
        },
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "content_package_123"


def test_content_package_route_returns_structured_status_and_result(monkeypatch) -> None:
    from src.entrypoints import content_package_routes

    monkeypatch.setattr(
        content_package_routes,
        "content_package_runtime_dependencies",
        lambda settings: type("Runtime", (), {"workflow_service": _ServiceStub()})(),
    )

    status_response = client.get("/api/content-packages/content_package_123")
    result_response = client.get("/api/content-packages/content_package_123/result")

    assert status_response.status_code == 200
    assert status_response.json()["job_id"] == "content_package_123"
    assert result_response.status_code == 200
    assert result_response.json()["version_id"] == "content_package_123_v1"
