"""Guardrails for the admin business account tier management UI."""

from pathlib import Path


def test_admin_business_accounts_page_exists_and_uses_typed_tier_actions() -> None:
    page_source = Path("apps/web/src/app/(admin)/admin/business-accounts/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/admin/business-accounts.tsx").read_text(encoding="utf-8")
    client_source = Path("apps/web/src/lib/api/client.ts").read_text(encoding="utf-8")
    contracts_source = Path("apps/web/src/lib/api/business-catalog-contracts.ts").read_text(encoding="utf-8")

    assert "AdminBusinessAccounts" in page_source
    assert "getAdminBusinessCatalogMerchantTiers" in feature_source
    assert "assignAdminBusinessCatalogMerchantTier" in feature_source
    assert "BusinessCatalogTenantTier" in contracts_source
    assert "AdminBusinessCatalogMerchantTierListResponse" in contracts_source
    assert "AdminAssignBusinessCatalogMerchantTierPayload" in contracts_source
    assert "getAdminBusinessCatalogMerchantTiers" in client_source
    assert "assignAdminBusinessCatalogMerchantTier" in client_source


def test_admin_business_accounts_page_is_locked_and_manual_approval_based() -> None:
    feature_source = Path("apps/web/src/features/admin/business-accounts.tsx").read_text(encoding="utf-8")
    workspace_routes_source = Path("apps/web/src/lib/routes/workspace-routes.ts").read_text(encoding="utf-8")

    assert "/admin/business-accounts" not in workspace_routes_source
    assert "NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI" in feature_source
    assert "Админ-панель выключена" in feature_source
    assert "Рекомендация системы" in feature_source
    assert "Назначенный tier" in feature_source
    assert "Причина решения" in feature_source
    assert "Перевести в large" in feature_source
    assert "Вернуть в standard" in feature_source
