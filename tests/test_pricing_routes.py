from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app
from src.domain.pricing import PricingJobRecord

client = TestClient(app)


class _DispatchStub:
    async def enqueue_workflow(self, **kwargs):
        return None


class _WorkerStub:
    async def run_one_cycle(self):
        return None


class _ServiceStub:
    async def create_pricing_job(self, *, request):
        return PricingJobRecord(
            job_id="pricing_123",
            product_id=request.product_id,
            target_currency=request.target_currency,
            desired_margin_percent=request.desired_margin_percent,
            status="accepted",
            created_at="2026-05-31T00:00:00+00:00",
            updated_at="2026-05-31T00:00:00+00:00",
        )

    async def get_job(self, job_id: str):
        return {
            "job_id": job_id,
            "product_id": "product-1",
            "target_currency": "RUB",
            "desired_margin_percent": 30.0,
            "status": "completed",
            "created_at": "2026-05-31T00:00:00+00:00",
            "updated_at": "2026-05-31T00:00:00+00:00",
        }

    async def get_result(self, job_id: str):
        return {
            "recommendation_id": f"{job_id}_v1",
            "job_id": job_id,
            "recommendation": {
                "recommended_price": 4727.7,
                "currency": "RUB",
                "rationale": "Positioned inside the observed comparable market band.",
                "market_min": 3990.0,
                "market_avg": 4590.0,
                "market_max": 5990.0,
            },
            "created_at": "2026-05-31T00:00:00+00:00",
        }


def test_pricing_route_returns_structured_recommendation(monkeypatch) -> None:
    from src.entrypoints import pricing_routes
    runtime = type("WorkflowRuntime", (), {"workflow_service": _ServiceStub()})()
    ops_runtime = type("OpsRuntime", (), {"dispatch_service": _DispatchStub(), "worker_runtime": _WorkerStub()})()

    monkeypatch.setattr(
        pricing_routes,
        "pricing_runtime_dependencies",
        lambda settings: runtime,
    )
    monkeypatch.setattr(pricing_routes, "operations_runtime_dependencies", lambda settings: ops_runtime)

    response = client.post(
        "/api/pricing-jobs",
        json={
            "product_id": "product-1",
            "target_currency": "RUB",
            "desired_margin_percent": 30.0,
        },
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "pricing_123"


def test_pricing_route_returns_structured_status_and_result(monkeypatch) -> None:
    from src.entrypoints import pricing_routes

    monkeypatch.setattr(
        pricing_routes,
        "pricing_runtime_dependencies",
        lambda settings: type("Runtime", (), {"workflow_service": _ServiceStub()})(),
    )

    status_response = client.get("/api/pricing-jobs/pricing_123")
    result_response = client.get("/api/pricing-jobs/pricing_123/result")

    assert status_response.status_code == 200
    assert status_response.json()["job_id"] == "pricing_123"
    assert result_response.status_code == 200
    assert result_response.json()["recommendation_id"] == "pricing_123_v1"
