"""Guardrails for the workspace settings page wiring."""

from pathlib import Path


def test_workspace_settings_page_reads_runtime_state() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/settings/page.tsx").read_text(encoding="utf-8")
    feature_source = Path("apps/web/src/features/workspace/workspace-settings-overview.tsx").read_text(encoding="utf-8")
    shell_loading_source = Path("apps/web/src/features/workspace/workspace-shell-loading.tsx").read_text(encoding="utf-8")
    shell_error_source = Path("apps/web/src/features/workspace/workspace-shell-error.tsx").read_text(encoding="utf-8")
    shell_empty_source = Path("apps/web/src/features/workspace/workspace-shell-empty.tsx").read_text(encoding="utf-8")
    shell_state_source = Path("apps/web/src/features/workspace/workspace-shell-state.tsx").read_text(encoding="utf-8")
    primitives_source = Path("apps/web/src/features/workspace/workspace-section-primitives.tsx").read_text(encoding="utf-8")
    hook_source = Path("apps/web/src/features/workspace/use-workspace-capability-verdict.ts").read_text(encoding="utf-8")

    assert "WorkspaceSettingsOverview" in page_source
    assert "useWorkspaceRuntime" in feature_source
    assert "useWorkspaceCapabilityVerdict" in feature_source
    assert "WorkspaceShellState" in feature_source
    assert "WorkspaceSectionCard" in feature_source
    assert "WorkspaceSettingsLoadingState" not in feature_source
    assert "WorkspaceSettingsErrorState" not in feature_source
    assert "WorkspaceSettingsEmptyState" not in feature_source
    assert "WorkspaceShellLoading" in shell_state_source
    assert "WorkspaceShellError" in shell_state_source
    assert "WorkspaceShellEmpty" in shell_state_source
    assert "WorkspaceSectionCard" in primitives_source
    assert "WorkspaceActionCard" in primitives_source
    assert "Workspace" in shell_error_source
    assert "bg-[var(--surface-alt)]" in shell_loading_source
    assert "workspace-page-title" in shell_empty_source
    assert "assertWorkspaceCapability" in hook_source
