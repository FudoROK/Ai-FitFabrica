"""Guardrails for the admin taxonomy review page."""

from pathlib import Path

from tests.frontend_api_sources import api_client_source


def test_admin_taxonomy_page_uses_typed_review_component() -> None:
    page_source = Path("apps/web/src/app/(admin)/admin/taxonomy/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/admin/taxonomy-review.tsx").read_text(encoding="utf-8")
    contracts_source = Path("apps/web/src/lib/api/admin-contracts.ts").read_text(encoding="utf-8")
    client_source = api_client_source()

    assert "AdminTaxonomyReview" in page_source
    assert "NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI" in feature_source
    assert "getAdminTaxonomyCandidates" in feature_source
    assert "approveAdminTaxonomyCandidate" in feature_source
    assert "rejectAdminTaxonomyCandidate" in feature_source
    assert "mergeAdminTaxonomyCandidate" in feature_source
    assert "renameAndApproveAdminTaxonomyCandidate" in feature_source
    assert "renameAndApproveAdminTaxonomyCandidate" in client_source
    assert "AdminRenameAndApproveTaxonomyCandidatePayload" in contracts_source
    assert "loading" in feature_source
    assert "empty" in feature_source
    assert "error" in feature_source
    assert "disabled" in feature_source
    assert "TaxonomyCandidateStatus" in contracts_source
    assert "AdminTaxonomyCandidate" in contracts_source
    assert "getAdminTaxonomyCandidates" in client_source
    assert "Admin access token" in feature_source
    assert "Authorization" in client_source
    assert "Bearer ${credentials.adminToken}" in client_source
    assert "x-fitfabrica-admin-role" not in client_source
    assert "x-fitfabrica-admin-id" not in client_source
