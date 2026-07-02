"""Guardrails for the workspace outfit-builder page wiring."""

from pathlib import Path


def test_workspace_outfit_builder_page_uses_backend_brief_and_request_contracts() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/outfit-builder/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/workspace/workspace-outfit-builder-overview.tsx").read_text(encoding="utf-8")
    client_source = Path("apps/web/src/lib/api/client.ts").read_text(encoding="utf-8")
    contracts_source = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")

    assert "WorkspaceOutfitBuilderOverview" in page_source
    assert "useWorkspaceRuntime" in feature_source
    assert "useEffect" in feature_source
    assert "getWorkspaceOutfitBuilderBrief" in feature_source
    assert "createWorkspaceOutfitBuilderRequest" in feature_source
    assert "getWorkspaceOutfitBuilderRequests" in feature_source
    assert "getWorkspaceOutfitBuilderRequestStatus" in feature_source
    assert "refresh" in feature_source
    assert "WorkspaceShellState" in feature_source
    assert "handleSubmit" in feature_source
    assert "getWorkspaceOutfitBuilderBrief" in client_source
    assert "createWorkspaceOutfitBuilderRequest" in client_source
    assert "getWorkspaceOutfitBuilderRequests" in client_source
    assert "getWorkspaceOutfitBuilderRequestStatus" in client_source
    assert "WorkspaceOutfitBuilderBriefResponse" in contracts_source
    assert "WorkspaceOutfitBuilderRequestListResponse" in contracts_source
    assert "WorkspaceOutfitBuilderRequestPayload" in contracts_source
    assert "WorkspaceOutfitBuilderRequestResponse" in contracts_source
    assert "WorkspaceOutfitBuilderRequestStatusResponse" in contracts_source
    assert "recentRequests" in feature_source
    assert "selectedStatus" in feature_source
