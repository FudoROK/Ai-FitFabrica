from pathlib import Path


API_DIR = Path("apps/web/src/lib/api")
CLIENT = API_DIR / "client.ts"
DOMAIN_CLIENTS = API_DIR / "clients"


def _api_client_sources() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(API_DIR.glob("**/*.ts")))


def test_web_api_client_is_a_small_compatibility_facade() -> None:
    source = CLIENT.read_text(encoding="utf-8")

    assert "export type WebApiClient" in source
    assert "export const WebApiClient" in source
    assert len(source.splitlines()) <= 260
    assert "new PublicApiClient" in source
    assert "new TryOnApiClient" in source
    assert "new WorkspaceApiClient" in source
    assert "new BusinessCatalogApiClient" in source
    assert "new AdminBusinessCatalogApiClient" in source
    assert "new WorkspaceCommerceApiClient" in source
    assert "new AdminTaxonomyApiClient" in source


def test_web_api_client_endpoints_are_kept_in_domain_clients() -> None:
    source = _api_client_sources()

    for endpoint in (
        "/auth/session",
        "/api/try-on/jobs",
        "/api/workspace/bootstrap",
        "/api/business/products",
        "/api/admin/business-catalog/discovery-candidates",
        "/api/workspace/outfit-builder/requests",
        "/api/similar-search/garment-photo",
        "/api/admin/taxonomy/candidates",
    ):
        assert endpoint in source

    assert (DOMAIN_CLIENTS / "public-client.ts").exists()
    assert (DOMAIN_CLIENTS / "try-on-client.ts").exists()
    assert (DOMAIN_CLIENTS / "workspace-client.ts").exists()
    assert (DOMAIN_CLIENTS / "business-catalog-client.ts").exists()
    assert (DOMAIN_CLIENTS / "admin-business-catalog-client.ts").exists()
    assert (DOMAIN_CLIENTS / "admin-business-catalog-discovery-client.ts").exists()
    assert (DOMAIN_CLIENTS / "admin-business-catalog-merchant-client.ts").exists()
    assert (DOMAIN_CLIENTS / "workspace-commerce-client.ts").exists()
    assert (DOMAIN_CLIENTS / "admin-taxonomy-client.ts").exists()
