"""Guardrails for unified workspace capability-aware calls to action."""

from pathlib import Path


def test_workspace_surfaces_use_capability_aware_ctas() -> None:
    component_source = Path(
        "apps/web/src/features/workspace/workspace-capability-cta.tsx"
    ).read_text(encoding="utf-8")
    sidebar_source = Path(
        "apps/web/src/components/navigation/workspace-sidebar.tsx"
    ).read_text(encoding="utf-8")
    dashboard_source = Path(
        "apps/web/src/features/workspace/dashboard/workspace-dashboard.tsx"
    ).read_text(encoding="utf-8")
    credits_source = Path(
        "apps/web/src/features/workspace/workspace-credits-view.tsx"
    ).read_text(encoding="utf-8")

    assert "WorkspaceCapabilityCta" in component_source
    assert "hasCapability(capability)" in component_source
    assert "disabled" in component_source
    assert "href={href}" in component_source
    assert 'capability="try_on_create"' in sidebar_source
    assert 'capability="business_profile_manage"' in dashboard_source
    assert 'capability="product_card_create"' in dashboard_source
    assert 'capability="try_on_create"' in credits_source
    assert 'capability="product_card_create"' in credits_source
