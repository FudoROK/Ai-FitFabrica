"""Guardrails for the workspace content-package page wiring."""

from pathlib import Path

from tests.frontend_api_sources import api_client_source


def test_workspace_content_package_page_uses_runtime_capability_gates() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/content-package/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/workspace/workspace-content-package-overview.tsx").read_text(encoding="utf-8")
    hook_source = Path("apps/web/src/features/workspace/use-workspace-capability-verdict.ts").read_text(encoding="utf-8")
    summary_panel_source = Path("apps/web/src/features/workspace/workspace-capability-summary-panel.tsx").read_text(encoding="utf-8")
    primitives_source = Path("apps/web/src/features/workspace/workspace-section-primitives.tsx").read_text(encoding="utf-8")
    client_source = api_client_source()

    assert "WorkspaceContentPackageOverview" in page_source
    assert "useWorkspaceRuntime" in feature_source
    assert 'hasCapability("manual_export")' in feature_source
    assert 'hasCapability("marketplace_publish")' in feature_source
    assert 'hasCapability("catalog_import")' in feature_source
    assert 'hasCapability("catalog_sync")' in feature_source
    assert "useWorkspaceCapabilityVerdict" in feature_source
    assert "WorkspaceCapabilitySummaryPanel" in feature_source
    assert "WorkspaceLockedProductionActions" in feature_source
    assert "WorkspaceActionCard" in feature_source
    assert "const summaryItems = [" in feature_source
    assert "summaryItems={summaryItems}" in feature_source
    assert "/workspace/integrations" in feature_source
    assert "assertWorkspaceCapability" in hook_source
    assert "summaryItems" in summary_panel_source
    assert "publishVerdict" in summary_panel_source
    assert "WorkspaceSectionCard" in primitives_source
    assert "WorkspaceActionCard" in primitives_source
    assert "assertWorkspaceCapability" in client_source
