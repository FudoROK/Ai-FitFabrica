from tests.admin_business_catalog_sources import ADMIN_BUSINESS_CATALOG_DIR, ADMIN_BUSINESS_CATALOG_ENTRY


def test_admin_business_catalog_review_is_split_by_responsibility() -> None:
    entry_source = ADMIN_BUSINESS_CATALOG_ENTRY.read_text(encoding="utf-8")

    assert len(entry_source.splitlines()) <= 620
    assert (ADMIN_BUSINESS_CATALOG_DIR / "model.ts").exists()
    assert (ADMIN_BUSINESS_CATALOG_DIR / "types.ts").exists()
    assert (ADMIN_BUSINESS_CATALOG_DIR / "shared-panels.tsx").exists()
    assert (ADMIN_BUSINESS_CATALOG_DIR / "discovery-candidate-review-panel.tsx").exists()
