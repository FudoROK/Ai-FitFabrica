"""Guardrails for the admin readiness diagnostics UI."""

from pathlib import Path


def test_admin_readiness_page_uses_typed_backend_ready_contract() -> None:
    page_source = Path("apps/web/src/app/(admin)/admin/readiness/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/admin/readiness-dashboard.tsx").read_text(encoding="utf-8")
    client_source = Path("apps/web/src/lib/api/client.ts").read_text(encoding="utf-8")
    contracts_source = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")

    assert "AdminReadinessDashboard" in page_source
    assert "NEXT_PUBLIC_ENABLE_ADMIN_READINESS_UI" in feature_source
    assert "getNoBillingReadiness" in feature_source
    assert "NoBillingReadinessResponse" in contracts_source
    assert "ReadinessServiceStatus" in contracts_source
    assert "getNoBillingReadiness" in client_source
    assert "/ready" in client_source
    assert "X-Status-Token" in client_source
    assert "safe_without_billing" in feature_source
    assert "post_billing_checks" in feature_source
    assert "blockers" in feature_source


def test_admin_readiness_page_is_internal_only_and_not_workspace_navigation() -> None:
    feature_source = Path("apps/web/src/features/admin/readiness-dashboard.tsx").read_text(encoding="utf-8")
    workspace_routes_source = Path("apps/web/src/lib/routes/workspace-routes.ts").read_text(encoding="utf-8")

    assert "/admin/readiness" not in workspace_routes_source
    assert "Admin readiness UI is disabled" in feature_source
    assert "statusToken" in feature_source
    assert "disabled={isLoading || statusToken.trim().length === 0}" in feature_source
