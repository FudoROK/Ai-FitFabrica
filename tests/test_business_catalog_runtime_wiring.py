from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.adapters.business_catalog import SandboxBusinessCatalogCategoryAnalyzer
from src.entrypoints.runtime_dependency_workflow_builders import build_business_catalog_service


def _settings(*, environment: str = "staging", validation_mode: str = "agent"):
    return SimpleNamespace(
        environment=environment,
        business_catalog_category_validation_mode=validation_mode,
        object_storage_prefix="fitfabrica",
    )


def _infrastructure():
    return SimpleNamespace(sql_session_factory=None, object_storage=object())


def test_business_catalog_service_uses_sandbox_category_analyzer_when_configured() -> None:
    service = build_business_catalog_service(
        _settings(validation_mode="sandbox"),
        infrastructure=_infrastructure(),
        agent_invocation_service=object(),
    )

    assert service._category_analyzer.__class__.__name__ == "SandboxBusinessCatalogCategoryAnalyzer"


def test_business_catalog_service_keeps_agent_category_analyzer_by_default() -> None:
    service = build_business_catalog_service(
        _settings(validation_mode="agent"),
        infrastructure=_infrastructure(),
        agent_invocation_service=object(),
    )

    assert service._category_analyzer.__class__.__name__ == "GarmentIdentityBusinessCatalogCategoryAnalyzer"


@pytest.mark.asyncio
async def test_sandbox_category_analyzer_covers_realistic_catalog_pack_names() -> None:
    analyzer = SandboxBusinessCatalogCategoryAnalyzer()

    cases = {
        "001_white_oversize_shirt.png": "shirt",
        "009_white_basic_tshirt.png": "tshirt",
        "011_ivory_longsleeve.png": "tshirt",
        "015_blue_straight_jeans.png": "pants",
        "016_black_tailored_trousers.png": "pants",
        "021_black_midi_dress.png": "dress",
        "026_beige_midi_skirt.png": "skirt",
        "026_beige_straight_blazer.png": "outerwear",
        "029_olive_quilted_jacket.png": "outerwear",
    }

    for filename, expected_category in cases.items():
        analysis = await analyzer.analyze_product_image(
            job_id="acceptance",
            object_key=f"fitfabrica/business-catalog/product/upload-digest/{filename}",
            content_type="image/png",
        )

        assert analysis.visual_category == expected_category
