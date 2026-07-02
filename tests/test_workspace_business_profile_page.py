"""Guardrails for the workspace business-profile page wiring."""

from pathlib import Path


def test_business_profile_page_uses_backend_api_and_runtime_refresh() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/business-profile/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/workspace/workspace-business-profile-form.tsx").read_text(encoding="utf-8")
    client_source = Path("apps/web/src/lib/api/client.ts").read_text(encoding="utf-8")
    contracts_source = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")

    assert "WorkspaceBusinessProfileForm" in page_source
    assert "useWorkspaceRuntime" in feature_source
    assert "refresh" in feature_source
    assert "display_name" in feature_source
    assert "channels" in feature_source
    assert "saveWorkspaceBusinessProfile" in client_source
    assert "getWorkspaceBusinessProfile" in client_source
    assert "WorkspaceBusinessProfilePayload" in contracts_source
    assert "WorkspaceBusinessProfileResponse" in contracts_source
