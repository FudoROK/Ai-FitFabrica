"""No-billing frontend readiness guardrails."""

from pathlib import Path
import re


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _frontend_sources() -> list[Path]:
    roots = [Path("apps/web/src/app"), Path("apps/web/src/features"), Path("apps/web/src/components")]
    return [path for root in roots for path in root.rglob("*") if path.suffix in {".ts", ".tsx"}]


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


def test_active_frontend_has_no_decorative_hash_links() -> None:
    """No active UI should ship placeholder anchors."""

    offenders: list[str] = []
    for path in _frontend_sources():
        source = path.read_text(encoding="utf-8")
        if 'href="#"' in source or "href='#'" in source:
            offenders.append(str(path))

    assert offenders == []


def test_active_frontend_forms_have_submit_handlers() -> None:
    """Forms must submit through real React handlers instead of rendering static markup."""

    offenders: list[str] = []
    form_pattern = re.compile(r"<form\\b(?![^>]*\\bonSubmit=)", re.MULTILINE)
    for path in _frontend_sources():
        source = path.read_text(encoding="utf-8")
        if form_pattern.search(source):
            offenders.append(str(path))

    assert offenders == []
