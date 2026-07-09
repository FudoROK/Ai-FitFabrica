from pathlib import Path


ADMIN_BUSINESS_CATALOG_DIR = Path("apps/web/src/features/admin/business-catalog-review")
ADMIN_BUSINESS_CATALOG_ENTRY = Path("apps/web/src/features/admin/business-catalog-review.tsx")


def admin_business_catalog_feature_source() -> str:
    sources = [ADMIN_BUSINESS_CATALOG_ENTRY.read_text(encoding="utf-8")]
    sources.extend(path.read_text(encoding="utf-8") for path in sorted(ADMIN_BUSINESS_CATALOG_DIR.glob("*.tsx")))
    sources.extend(path.read_text(encoding="utf-8") for path in sorted(ADMIN_BUSINESS_CATALOG_DIR.glob("*.ts")))
    return "\n".join(sources)
