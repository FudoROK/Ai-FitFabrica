from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app
from src.domain.product_card import ProductCardJobRecord

client = TestClient(app)


class _DispatchStub:
    async def enqueue_workflow(self, **kwargs):
        return None


class _WorkerStub:
    async def run_one_cycle(self):
        return None


class _ServiceStub:
    async def create_product_card_job(self, *, request, source_files):
        return ProductCardJobRecord(
            job_id="product_card_123",
            status="accepted",
            target_channel=request.target_channel,
            brand_tone=request.brand_tone,
            title_hint=request.title_hint,
            asset_keys=[f"tenant/product-card/{item.filename}" for item in source_files],
            created_at="2026-05-31T00:00:00+00:00",
            updated_at="2026-05-31T00:00:00+00:00",
        )

    async def get_job(self, job_id: str):
        return {
            "job_id": job_id,
            "status": "completed",
            "target_channel": "wildberries",
            "brand_tone": "minimal premium",
            "title_hint": "Linen midi dress",
            "asset_keys": ["tenant/product-card/source-1.png"],
            "created_at": "2026-05-31T00:00:00+00:00",
            "updated_at": "2026-05-31T00:00:00+00:00",
        }

    async def get_result(self, job_id: str):
        return {
            "version_id": f"{job_id}_v1",
            "job_id": job_id,
            "title": "Linen midi dress",
            "description": "Breathable summer dress with a clean silhouette.",
            "bullet_points": ["linen blend", "midi length"],
            "attributes": {"category": "dress"},
            "created_at": "2026-05-31T00:00:00+00:00",
        }


def test_product_card_route_creates_job_and_returns_structured_response(monkeypatch) -> None:
    from src.entrypoints import product_card_routes
    runtime = type("WorkflowRuntime", (), {"workflow_service": _ServiceStub()})()
    ops_runtime = type("OpsRuntime", (), {"dispatch_service": _DispatchStub(), "worker_runtime": _WorkerStub()})()

    monkeypatch.setattr(
        product_card_routes,
        "product_card_runtime_dependencies",
        lambda settings: runtime,
    )
    monkeypatch.setattr(product_card_routes, "operations_runtime_dependencies", lambda settings: ops_runtime)

    response = client.post(
        "/api/product-cards",
        json={
            "title_hint": "Linen midi dress",
            "target_channel": "wildberries",
            "brand_tone": "minimal premium",
            "source_files": [
                {
                    "filename": "source-1.png",
                    "content_type": "image/png",
                    "payload_base64": "aW1hZ2UtYnl0ZXM=",
                }
            ],
        },
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "product_card_123"


def test_product_card_route_returns_structured_status_and_result(monkeypatch) -> None:
    from src.entrypoints import product_card_routes

    monkeypatch.setattr(
        product_card_routes,
        "product_card_runtime_dependencies",
        lambda settings: type("Runtime", (), {"workflow_service": _ServiceStub()})(),
    )

    status_response = client.get("/api/product-cards/product_card_123")
    result_response = client.get("/api/product-cards/product_card_123/result")

    assert status_response.status_code == 200
    assert status_response.json()["job_id"] == "product_card_123"
    assert result_response.status_code == 200
    assert result_response.json()["version_id"] == "product_card_123_v1"
