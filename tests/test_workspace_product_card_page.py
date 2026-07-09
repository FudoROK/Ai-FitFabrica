"""Guardrails for the workspace product-card page wiring."""

from pathlib import Path

from tests.frontend_api_sources import api_client_source


def test_workspace_product_card_page_uses_runtime_capability_gates() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/product-card/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/workspace/workspace-product-card-overview.tsx").read_text(encoding="utf-8")
    workflow_source = Path("apps/web/src/features/workspace/product-card-workflow.tsx").read_text(encoding="utf-8")
    client_source = api_client_source()

    assert "WorkspaceProductCardOverview" in page_source
    assert "useWorkspaceRuntime" in feature_source
    assert 'hasCapability("business_templates")' in feature_source
    assert 'hasCapability("marketplace_publish")' in feature_source
    assert 'hasCapability("catalog_import")' in feature_source
    assert 'hasCapability("catalog_sync")' in feature_source
    assert "ProductCardWorkflow" in feature_source
    assert 'workspaceHasCapability("product_card_create")' in workflow_source
    assert "workflow_costs.product_card" in workflow_source
    assert "bootstrap.credits.balance" in workflow_source
    assert "createProductCardJob" in workflow_source
    assert "getProductCardJob" in workflow_source
    assert "getProductCardResult" in workflow_source
    assert 'accept="image/jpeg,image/png,image/webp"' in workflow_source
    assert 'name="category"' in workflow_source
    assert 'name="target_channel"' in workflow_source
    assert 'name="brand_tone"' in workflow_source
    assert "disabled={!canSubmit}" in workflow_source
    assert "createProductCardJob" in client_source
    assert "getProductCardJob" in client_source
    assert "getProductCardResult" in client_source
    assert "pending_workspace_product_card" not in feature_source
    assert "pending_workspace_content_package" not in feature_source
    assert "useWorkspaceGuardedActions" not in feature_source
    assert "WorkspaceGuardedActionsPanel" not in feature_source
