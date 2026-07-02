"""Guardrails for the workspace integrations page wiring."""

from pathlib import Path


def test_workspace_integrations_page_uses_backend_api_and_runtime_refresh() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/integrations/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/workspace/workspace-integrations-form.tsx").read_text(encoding="utf-8")
    hook_source = Path("apps/web/src/features/workspace/use-workspace-capability-verdict.ts").read_text(encoding="utf-8")
    client_source = Path("apps/web/src/lib/api/client.ts").read_text(encoding="utf-8")
    contracts_source = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")

    assert "WorkspaceIntegrationsForm" in page_source
    assert "useWorkspaceRuntime" in feature_source
    assert "refresh" in feature_source
    assert "connected_channels" in feature_source
    assert "has_connected_store" in feature_source
    assert "saveWorkspaceIntegrations" in client_source
    assert "getWorkspaceIntegrations" in client_source
    assert "useWorkspaceCapabilityVerdict" in feature_source
    assert "WorkspaceIntegrationsPayload" in contracts_source
    assert "WorkspaceIntegrationsResponse" in contracts_source
    assert "WorkspaceCapabilityMatrixResponse" in contracts_source
    assert "getWorkspaceCapabilities" in hook_source
