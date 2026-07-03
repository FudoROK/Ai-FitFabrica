"""No-billing frontend readiness guardrails."""

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_public_ctas_use_canonical_contact_route() -> None:
    """Public CTAs should point to /contact; /contacts stays only as a legacy alias page."""

    checked_paths = [
        "apps/web/src/app/(public)/business/page.tsx",
        "apps/web/src/app/(public)/pricing/page.tsx",
        "apps/web/src/lib/content/public-pages.ts",
        "apps/web/src/lib/content/public-pages-extra.ts",
        "apps/web/src/lib/content/workspace-pages-extra.ts",
    ]

    for path in checked_paths:
        source = _read(path)
        assert 'href="/contacts"' not in source
        assert 'href: "/contacts"' not in source


def test_active_workspace_pages_do_not_render_blank_when_bootstrap_is_missing() -> None:
    """Active workspace pages should use shell states instead of silently returning null."""

    checked_paths = [
        "apps/web/src/app/(workspace)/workspace/history/page.tsx",
        "apps/web/src/app/(workspace)/workspace/projects/page.tsx",
        "apps/web/src/features/workspace/product-card-workflow.tsx",
        "apps/web/src/features/workspace/workspace-content-package-overview.tsx",
        "apps/web/src/features/workspace/workspace-product-card-overview.tsx",
    ]

    for path in checked_paths:
        source = _read(path)
        assert "return null" not in source
        assert "WorkspaceShellState" in source
