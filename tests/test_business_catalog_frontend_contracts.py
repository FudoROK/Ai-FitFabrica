from pathlib import Path

from tests.frontend_api_sources import api_client_source


CONTRACTS = Path("apps/web/src/lib/api/business-catalog-contracts.ts")


def test_business_catalog_frontend_contracts_are_typed() -> None:
    source = CONTRACTS.read_text(encoding="utf-8")

    required_types = (
        "BusinessMerchantResponse",
        "BusinessProductResponse",
        "BusinessProductListResponse",
        "BusinessProductCreatePayload",
        "BusinessProductImageResponse",
        "BusinessCatalogImportResponse",
        "BusinessCatalogImportJobResponse",
        "BusinessCatalogImportErrorsResponse",
    )
    for type_name in required_types:
        assert f"export type {type_name}" in source

    assert "any" not in source


def test_business_catalog_frontend_client_exposes_real_backend_methods() -> None:
    source = api_client_source()

    for method_name in (
        "getBusinessMerchant",
        "saveBusinessMerchant",
        "listBusinessProducts",
        "createBusinessProduct",
        "submitBusinessProduct",
        "uploadBusinessProductImage",
        "retryAdminBusinessCatalogProductSearchIndex",
        "createBusinessCatalogImport",
        "getBusinessCatalogImport",
        "getBusinessCatalogImportErrors",
    ):
        assert f"public async {method_name}" in source

    assert "/api/business/merchant" in source
    assert "/api/business/products" in source
    assert "/api/business/catalog-imports" in source
