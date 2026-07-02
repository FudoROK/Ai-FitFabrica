from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.garment_taxonomy import GarmentTaxonomyItem, GarmentWearControl, GarmentWearControlRiskLevel
from src.entrypoints.garment_taxonomy_routes import router
from src.use_cases.garment_taxonomy.service import AvailableWearControlsResult


class _TaxonomyService:
    async def resolve_available_controls(self, *, garment_type: str, unknown_input=None):
        item = GarmentTaxonomyItem(code=garment_type, category="tops", display_name="Shirt")
        return AvailableWearControlsResult(
            taxonomy_item=item,
            available_controls=[
                GarmentWearControl(
                    control_code="untucked",
                    display_name="Untucked",
                    description="Wear the shirt over the waistband.",
                    instruction_template="Keep the shirt hem visible over the lower garment.",
                    taxonomy_item_code=item.code,
                    risk_level=GarmentWearControlRiskLevel.LOW,
                    default_for_auto=True,
                ),
                GarmentWearControl(
                    control_code="tucked",
                    display_name="Tucked",
                    description="Tuck the shirt into the waistband.",
                    instruction_template="Place the shirt hem inside the lower garment waistband.",
                    taxonomy_item_code=item.code,
                    risk_level=GarmentWearControlRiskLevel.MEDIUM,
                ),
            ],
        )


def _client(monkeypatch, service: _TaxonomyService | None) -> TestClient:
    app = FastAPI()
    app.state.settings = SimpleNamespace()
    app.include_router(router)
    monkeypatch.setattr(
        "src.entrypoints.garment_taxonomy_routes.garment_taxonomy_service",
        lambda settings: service,
    )
    return TestClient(app)


def test_garment_taxonomy_wear_controls_are_read_only_workspace_contract(monkeypatch) -> None:
    client = _client(monkeypatch, _TaxonomyService())

    response = client.get("/api/garment-taxonomy/wear-controls?garment_type=shirt")

    assert response.status_code == 200
    payload = response.json()
    assert payload["garment_type"] == "shirt"
    assert payload["taxonomy_item_code"] == "shirt"
    assert payload["created_candidate"] is False
    assert payload["controls"] == [
        {
            "control_code": "untucked",
            "display_name": "Untucked",
            "description": "Wear the shirt over the waistband.",
            "instruction_template": "Keep the shirt hem visible over the lower garment.",
            "risk_level": "low",
            "default_for_auto": True,
        },
        {
            "control_code": "tucked",
            "display_name": "Tucked",
            "description": "Tuck the shirt into the waistband.",
            "instruction_template": "Place the shirt hem inside the lower garment waistband.",
            "risk_level": "medium",
            "default_for_auto": False,
        },
    ]


def test_garment_taxonomy_wear_controls_require_taxonomy_storage(monkeypatch) -> None:
    client = _client(monkeypatch, None)

    response = client.get("/api/garment-taxonomy/wear-controls?garment_type=shirt")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "garment_taxonomy_storage_unavailable"
