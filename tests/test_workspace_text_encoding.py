"""Guardrails for frontend UI text encoding."""

from pathlib import Path


TARGET_FILES = [
    "apps/web/src/app/(public)/business/page.tsx",
    "apps/web/src/app/(public)/capabilities/page.tsx",
    "apps/web/src/app/(public)/contacts/page.tsx",
    "apps/web/src/app/(public)/for-you/page.tsx",
    "apps/web/src/app/(public)/how-it-works/page.tsx",
    "apps/web/src/app/(public)/page.tsx",
    "apps/web/src/app/(public)/pricing/page.tsx",
    "apps/web/src/app/(public)/privacy/page.tsx",
    "apps/web/src/features/public/contact-form.tsx",
    "apps/web/src/features/public/sign-in-form.tsx",
    "apps/web/src/app/(workspace)/workspace/history/page.tsx",
    "apps/web/src/app/(workspace)/workspace/outfit-builder/page.tsx",
    "apps/web/src/app/(workspace)/workspace/projects/page.tsx",
    "apps/web/src/features/workspace/dashboard/workspace-dashboard.tsx",
    "apps/web/src/features/workspace/try-on-result.tsx",
    "apps/web/src/features/workspace/try-on-workflow.tsx",
    "apps/web/src/features/workspace/workspace-business-profile-form.tsx",
    "apps/web/src/features/workspace/workspace-content-package-overview.tsx",
    "apps/web/src/features/workspace/workspace-credits-view.tsx",
    "apps/web/src/features/workspace/workspace-integrations-form.tsx",
    "apps/web/src/features/workspace/workspace-product-card-overview.tsx",
    "apps/web/src/features/workspace/workspace-runtime.tsx",
    "apps/web/src/features/workspace/workspace-settings-overview.tsx",
    "apps/web/src/features/workspace/workspace-shell-error.tsx",
    "apps/web/src/lib/content/public-pages.ts",
    "apps/web/src/lib/content/workspace-pages.ts",
]

MOJIBAKE_MARKERS = [
    "Р ",
    "РЎ",
    "Рќ",
    "СЏ",
    "С‚",
    "СЊ",
    "вЂ”",
]


def test_frontend_ui_files_do_not_contain_mojibake_sequences() -> None:
    for relative_path in TARGET_FILES:
        source = Path(relative_path).read_text(encoding="utf-8")
        for marker in MOJIBAKE_MARKERS:
            assert marker not in source, f"{relative_path} still contains mojibake marker {marker!r}"
