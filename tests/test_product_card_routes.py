from __future__ import annotations

import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.domain.billing import BillingOwnerType, CreditAccount
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
            category=request.category,
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
            "category": "dress",
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

    async def get_garment_analysis(self, job_id: str):
        return {
            "job_id": job_id,
            "invocation_id": "garment-invocation-1",
            "prompt_version": "garment_identity.v1",
            "contract_version": "garment_identity.contract.v1",
            "garment_type": "dress",
            "dominant_color": "blue",
            "secondary_colors": [],
            "silhouette_summary": "Midi dress.",
            "preserved_details": [],
            "confidence": 0.95,
            "limitations": [],
            "visual_details": [],
            "evidence": [],
            "uncertainty_level": "low",
            "unknowns": [],
            "completed_at": "2026-06-15T00:00:00+00:00",
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
            "category": "dress",
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
    assert response.json()["category"] == "dress"


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


def test_product_card_route_returns_saved_garment_analysis(monkeypatch) -> None:
    from src.entrypoints import product_card_routes

    monkeypatch.setattr(
        product_card_routes,
        "product_card_runtime_dependencies",
        lambda settings: type("Runtime", (), {"workflow_service": _ServiceStub()})(),
    )

    response = client.get("/api/product-cards/product_card_123/garment-analysis")

    assert response.status_code == 200
    assert response.json()["garment_type"] == "dress"


def test_product_card_route_rejects_create_when_capability_is_denied(monkeypatch) -> None:
    from src.entrypoints import product_card_routes
    from src.use_cases.workspace.capability_service import WorkspaceCapabilityDeniedError

    class _CapabilityServiceStub:
        async def require_capability(self, *, owner_id: str, capability: str) -> None:
            raise WorkspaceCapabilityDeniedError(capability=capability, reason="Product card creation is disabled.")

    monkeypatch.setattr(product_card_routes, "workspace_capability_service", lambda settings: _CapabilityServiceStub())

    response = client.post(
        "/api/product-cards",
        json={
            "title_hint": "Linen midi dress",
            "category": "dress",
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

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "workspace_capability_denied"


def test_product_card_credit_preflight_rejects_insufficient_balance(monkeypatch) -> None:
    from src.entrypoints import product_card_routes

    class _BillingServiceStub:
        async def get_account_balance(self, *, owner_id: str, owner_type: BillingOwnerType) -> CreditAccount:
            return CreditAccount(owner_id=owner_id, owner_type=owner_type, available_credits=4, reserved_credits=0)

    runtime = SimpleNamespace(billing_service=_BillingServiceStub())
    monkeypatch.setattr(product_card_routes, "billing_runtime_dependencies", lambda settings: runtime)
    settings = SimpleNamespace(
        billing_core_enabled=True,
        default_person_credit_account_id="public-person",
        product_card_base_credit_cost=18,
    )

    response = asyncio.run(product_card_routes._require_product_card_credits(settings))

    assert response is not None
    assert response.status_code == 402


def test_product_card_route_rejects_non_image_source_file() -> None:
    response = client.post(
        "/api/product-cards",
        json={
            "title_hint": "Linen midi dress",
            "category": "dress",
            "target_channel": "wildberries",
            "brand_tone": "minimal premium",
            "source_files": [
                {
                    "filename": "source.txt",
                    "content_type": "text/plain",
                    "payload_base64": "dGV4dA==",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_product_card_route_requires_title() -> None:
    response = client.post(
        "/api/product-cards",
        json={
            "category": "dress",
            "target_channel": "wildberries",
            "brand_tone": "minimal premium",
            "source_files": [
                {
                    "filename": "source.png",
                    "content_type": "image/png",
                    "payload_base64": "aW1hZ2U=",
                }
            ],
        },
    )

    assert response.status_code == 422
