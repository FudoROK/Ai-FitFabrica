"""Guardrails for the workspace business catalog UI wiring."""

from pathlib import Path


FEATURE_DIR = Path("apps/web/src/features/workspace/business-catalog")


def test_workspace_business_catalog_pages_exist_and_use_real_api_client() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/business-catalog/page.tsx").read_text(encoding="utf-8")
    new_page_source = Path("apps/web/src/app/(workspace)/workspace/business-catalog/new/page.tsx").read_text(encoding="utf-8")
    import_page_source = Path("apps/web/src/app/(workspace)/workspace/business-catalog/import/page.tsx").read_text(encoding="utf-8")
    overview_source = (FEATURE_DIR / "business-catalog-page.tsx").read_text(encoding="utf-8")
    form_source = (FEATURE_DIR / "business-product-form.tsx").read_text(encoding="utf-8")
    import_source = (FEATURE_DIR / "business-catalog-import-page.tsx").read_text(encoding="utf-8")
    routes_source = Path("apps/web/src/lib/routes/workspace-routes.ts").read_text(encoding="utf-8")

    assert "BusinessCatalogPage" in page_source
    assert "BusinessProductForm" in new_page_source
    assert "BusinessCatalogImportPage" in import_page_source
    assert "getBusinessMerchant" in overview_source
    assert "listBusinessProducts" in overview_source
    assert "createBusinessProduct" in form_source
    assert "uploadBusinessProductImage" in form_source
    assert "createBusinessCatalogImport" in import_source
    assert "/workspace/business-catalog" in routes_source


def test_workspace_business_catalog_ui_has_required_states_and_validation() -> None:
    combined = "\n".join(
        [
            (FEATURE_DIR / "business-catalog-page.tsx").read_text(encoding="utf-8"),
            (FEATURE_DIR / "business-product-form.tsx").read_text(encoding="utf-8"),
            (FEATURE_DIR / "business-catalog-import-page.tsx").read_text(encoding="utf-8"),
        ]
    )

    for required_text in (
        "Каталог товаров",
        "Название товара",
        "Категория",
        "Цена",
        "Страна",
        "Город",
        "Фото товара",
        "CSV-файл",
        "Загрузка каталога",
        "Пока нет товаров",
        "Не удалось загрузить",
        "Товар создан",
        "Импорт завершён",
        "Поддерживаются JPEG, PNG и WEBP до 10 MB",
        "Проверка категории",
        "Категория совпала с фото",
        "Категория не совпала с фото",
        "Нужна ручная проверка категории",
        "Видимость в поиске",
        "Доступен в локальном поиске",
        "Ожидает админ-проверку",
        "Индексация ещё не завершена",
        "Не попадёт в поиск",
        "disabled={!canSubmit}",
    ):
        assert required_text in combined

    assert "marketplace_publish" not in combined
    assert "catalog_sync" not in combined
    assert "href=\"#\"" not in combined
    assert "pending_workspace" not in combined


def test_workspace_business_catalog_ui_explains_upload_limits() -> None:
    combined = "\n".join(
        [
            (FEATURE_DIR / "business-product-form.tsx").read_text(encoding="utf-8"),
            (FEATURE_DIR / "business-catalog-import-page.tsx").read_text(encoding="utf-8"),
        ]
    )

    for required_text in (
        "CSV limits",
        "standard: 1,000 rows / 5 MB",
        "large: 25,000 rows / 50 MB",
        "Upload requirements",
        "JPG, PNG, WEBP up to 10 MB",
        "Detailed upload limits",
        "Фото должно показывать тот же тип одежды, который указан в категории",
        "Если категория не совпадает с фото, товар не попадёт в поиск до исправления",
    ):
        assert required_text in combined
