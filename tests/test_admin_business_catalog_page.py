"""Guardrails for the admin business catalog review UI."""

from pathlib import Path

from tests.frontend_api_sources import api_client_source


def test_admin_business_catalog_page_exists_and_uses_typed_actions() -> None:
    page_source = Path("apps/web/src/app/(admin)/admin/business-catalog/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/admin/business-catalog-review.tsx").read_text(encoding="utf-8")
    client_source = api_client_source()
    contracts_source = Path("apps/web/src/lib/api/business-catalog-contracts.ts").read_text(encoding="utf-8")

    assert "AdminBusinessCatalogReview" in page_source
    assert "getAdminBusinessCatalogPendingProducts" in feature_source
    assert "approveAdminBusinessCatalogProduct" in feature_source
    assert "rejectAdminBusinessCatalogProduct" in feature_source
    assert "getAdminSimilarSearchAnalytics" in feature_source
    assert "SimilarSearchAnalyticsPanel" in feature_source
    assert "Similar Search Analytics" in feature_source
    assert "getAdminMarketplaceDiscoveryCandidates" in feature_source
    assert "approveAdminMarketplaceDiscoveryCandidate" in feature_source
    assert "rejectAdminMarketplaceDiscoveryCandidate" in feature_source
    assert "archiveAdminMarketplaceDiscoveryCandidate" in feature_source
    assert "Discovery Candidates" in feature_source
    assert "DiscoveryCandidateReviewPanel" in feature_source
    assert "DiscoveryCandidateFilters" in feature_source
    assert "Reject reason" in feature_source
    assert "source_url" in feature_source
    assert "marketplace candidates discovered from approved search sources" in feature_source
    assert "getBusinessProductReviewReadiness" in feature_source
    assert "getBusinessProductReviewSummary" in feature_source
    assert "Review readiness" in feature_source
    assert "Review queue summary" in feature_source
    assert "Ready to approve" in feature_source
    assert "Needs AI validation" in feature_source
    assert "Blocked by category" in feature_source
    assert "Indexing issues" in feature_source
    assert "Review filter" in feature_source
    assert "ready_to_approve" in feature_source
    assert "needs_ai_validation" in feature_source
    assert "blocked_by_category" in feature_source
    assert "indexing_issues" in feature_source
    assert "Admin operation order" in feature_source
    assert "1. Run AI validation batch" in feature_source
    assert "2. Approve matched batch" in feature_source
    assert "3. Check indexing status" in feature_source
    assert "Do not approve mismatched or uncertain products." in feature_source
    assert "Bulk operation details" in feature_source
    assert "lastBulkOperation" in feature_source
    assert "product_id" in feature_source
    assert "error_message" in feature_source
    assert "Clear bulk result" in feature_source
    assert "onClear" in feature_source
    assert "StatusBadge" in feature_source
    assert "getStatusBadgeTone" in feature_source
    assert "bg-emerald-50" in feature_source
    assert "bg-rose-50" in feature_source
    assert "bg-amber-50" in feature_source
    assert "Run AI validation before approval." in feature_source
    assert "Fix category mismatch or reject/archive the product." in feature_source
    assert "Product is ready for approve." in feature_source
    assert "reason" in feature_source
    assert "NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI" in feature_source
    assert "AdminBusinessCatalogCredentials" in contracts_source
    assert "AdminBusinessCatalogPendingProductsResponse" in contracts_source
    assert "AdminMarketplaceDiscoveryCandidate" in contracts_source
    assert "AdminMarketplaceDiscoveryCandidateStatus" in contracts_source
    assert "AdminMarketplaceDiscoveryCandidateListResponse" in contracts_source
    assert "AdminRejectMarketplaceDiscoveryCandidatePayload" in contracts_source
    assert "AdminRejectBusinessCatalogProductPayload" in contracts_source
    assert "SimilarSearchClickAnalyticsResponse" in contracts_source
    assert "getAdminBusinessCatalogPendingProducts" in client_source
    assert "approveAdminBusinessCatalogProduct" in client_source
    assert "rejectAdminBusinessCatalogProduct" in client_source
    assert "getAdminSimilarSearchAnalytics" in client_source
    assert "getAdminMarketplaceDiscoveryCandidates" in client_source
    assert "approveAdminMarketplaceDiscoveryCandidate" in client_source
    assert "rejectAdminMarketplaceDiscoveryCandidate" in client_source
    assert "archiveAdminMarketplaceDiscoveryCandidate" in client_source


def test_admin_business_catalog_page_is_not_public_workspace_action() -> None:
    workspace_routes_source = Path("apps/web/src/lib/routes/workspace-routes.ts").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/admin/business-catalog-review.tsx").read_text(encoding="utf-8")

    assert "/admin/business-catalog" not in workspace_routes_source
    assert "Админ-панель выключена" in feature_source
    assert "Нет товаров на проверке" in feature_source
    assert "Причина отклонения" in feature_source
