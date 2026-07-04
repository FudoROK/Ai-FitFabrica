"""B2C/B2B client readiness gate for pre-billing preparation."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXTERNAL_BLOCKERS = [
    "production_auth_activation",
    "billing_core_activation",
    "live_ai_provider_acceptance",
    "approved_marketplace_source_activation",
    "deployed_staging_browser_acceptance",
]


def build_flow_matrix() -> list[dict[str, object]]:
    """Return customer-facing flows that must be ready before billing is enabled."""

    return [
        {
            "id": "b2c_public_entry",
            "audience": "b2c",
            "ui_routes": [
                "apps/web/src/app/(public)/page.tsx",
                "apps/web/src/app/(public)/for-you/page.tsx",
                "apps/web/src/app/(public)/contact/page.tsx",
                "apps/web/src/app/(public)/login/page.tsx",
            ],
            "api_contracts": ["POST /demo-request", "POST /auth/sign-in"],
            "api_files": ["src/entrypoints/public_request_routes.py"],
            "tests": ["tests/test_public_request_routes.py", "tests/test_public_frontend_routes.py"],
            "ready_without_billing": True,
        },
        {
            "id": "b2c_try_on",
            "audience": "b2c",
            "ui_routes": [
                "apps/web/src/app/(workspace)/workspace/new-fitting/page.tsx",
                "apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx",
                "apps/web/src/app/(workspace)/workspace/try-on/result/page.tsx",
            ],
            "api_contracts": ["POST /api/try-on/jobs"],
            "api_files": ["src/entrypoints/try_on_routes.py"],
            "tests": [
                "tests/test_try_on_runtime_wiring.py",
                "tests/test_try_on_sql_repository.py",
                "tests/test_workspace_try_on_multi_garment_page.py",
            ],
            "ready_without_billing": True,
        },
        {
            "id": "b2c_similar_search",
            "audience": "b2c",
            "ui_routes": ["apps/web/src/app/(workspace)/workspace/similar-search/page.tsx"],
            "api_contracts": ["POST /api/similar-search", "POST /api/similar-search/garment-photo"],
            "api_files": ["src/entrypoints/similar_search_routes.py"],
            "tests": [
                "tests/test_similar_search_routes.py",
                "tests/test_similar_search_runtime_wiring.py",
                "tests/test_workspace_similar_search_page.py",
            ],
            "ready_without_billing": True,
        },
        {
            "id": "b2c_outfit_builder",
            "audience": "b2c",
            "ui_routes": ["apps/web/src/app/(workspace)/workspace/outfit-builder/page.tsx"],
            "api_contracts": ["/api/workspace/outfit-builder/requests"],
            "api_files": ["src/entrypoints/outfit_builder_routes.py"],
            "tests": [
                "tests/test_workspace_outfit_builder_routes.py",
                "tests/test_workspace_outfit_builder_page.py",
            ],
            "ready_without_billing": True,
        },
        {
            "id": "b2b_business_catalog",
            "audience": "b2b",
            "ui_routes": [
                "apps/web/src/app/(workspace)/workspace/business-catalog/page.tsx",
                "apps/web/src/app/(workspace)/workspace/business-catalog/new/page.tsx",
                "apps/web/src/app/(workspace)/workspace/business-catalog/import/page.tsx",
            ],
            "api_contracts": ["/api/business"],
            "api_files": ["src/entrypoints/business_catalog_routes.py"],
            "tests": [
                "tests/test_business_catalog_routes.py",
                "tests/test_business_catalog_runtime_wiring.py",
                "tests/test_business_catalog_sql_repository.py",
            ],
            "ready_without_billing": True,
        },
        {
            "id": "b2b_product_card",
            "audience": "b2b",
            "ui_routes": ["apps/web/src/app/(workspace)/workspace/product-card/page.tsx"],
            "api_contracts": ["POST /api/product-cards"],
            "api_files": ["src/entrypoints/product_card_routes.py"],
            "tests": [
                "tests/test_product_card_routes.py",
                "tests/test_product_card_runtime_wiring.py",
                "tests/test_product_card_sql_repositories.py",
            ],
            "ready_without_billing": True,
        },
        {
            "id": "b2b_content_package",
            "audience": "b2b",
            "ui_routes": ["apps/web/src/app/(workspace)/workspace/content-package/page.tsx"],
            "api_contracts": ["POST /api/content-packages"],
            "api_files": ["src/entrypoints/content_package_routes.py"],
            "tests": [
                "tests/test_content_package_routes.py",
                "tests/test_content_package_runtime_wiring.py",
                "tests/test_content_package_sql_repositories.py",
            ],
            "ready_without_billing": True,
        },
        {
            "id": "b2b_pricing",
            "audience": "b2b",
            "ui_routes": ["apps/web/src/app/(workspace)/workspace/projects/page.tsx"],
            "api_contracts": ["POST /api/pricing-jobs"],
            "api_files": ["src/entrypoints/pricing_routes.py"],
            "tests": [
                "tests/test_pricing_routes.py",
                "tests/test_pricing_runtime_wiring.py",
                "tests/test_pricing_sql_repositories.py",
            ],
            "ready_without_billing": True,
        },
        {
            "id": "b2b_admin_review",
            "audience": "b2b_admin",
            "ui_routes": [
                "apps/web/src/app/(admin)/admin/readiness/page.tsx",
                "apps/web/src/app/(admin)/admin/business-catalog/page.tsx",
                "apps/web/src/app/(admin)/admin/taxonomy/page.tsx",
                "apps/web/src/app/(admin)/admin/business-accounts/page.tsx",
            ],
            "api_contracts": ["/api/admin/business-catalog", "/api/admin/taxonomy"],
            "api_files": [
                "src/entrypoints/admin_business_catalog_routes.py",
                "src/entrypoints/admin_taxonomy_routes.py",
                "src/entrypoints/admin_cost_routes.py",
            ],
            "tests": [
                "tests/test_admin_business_catalog_routes.py",
                "tests/test_admin_taxonomy_routes.py",
                "tests/test_admin_readiness_page.py",
            ],
            "ready_without_billing": True,
        },
    ]


def run_gate() -> dict[str, object]:
    """Check local artifacts that prove B2C/B2B client contours are prepared."""

    flow_reports = [_check_flow(flow) for flow in build_flow_matrix()]
    failed_checks = [str(report["id"]) for report in flow_reports if report["status"] != "passed"]
    return {
        "gate": "client_readiness",
        "readiness_status": "blocked" if failed_checks else "ready",
        "failed_checks": failed_checks,
        "external_blockers": EXTERNAL_BLOCKERS,
        "flows": flow_reports,
        "next_commands": [
            "python scripts/no_billing_acceptance_gate.py --full-backend",
            "python scripts/staging_no_billing_smoke.py --api-base-url <api> --web-base-url <web> --status-token <token>",
            "python scripts/post_billing_acceptance_gate.py --api-base-url <api> --status-token <token> --require-ready",
        ],
    }


def _check_flow(flow: dict[str, object]) -> dict[str, object]:
    """Return one flow readiness report."""

    missing_ui = _missing_paths(flow["ui_routes"])
    missing_api_files = _missing_paths(flow["api_files"])
    missing_tests = _missing_paths(flow["tests"])
    missing_contracts = _missing_api_contracts(flow["api_contracts"], flow["api_files"])
    missing = missing_ui + missing_api_files + missing_tests + missing_contracts
    return {
        "id": flow["id"],
        "audience": flow["audience"],
        "status": "failed" if missing else "passed",
        "ready_without_billing": flow["ready_without_billing"],
        "missing": missing,
        "ui_routes": flow["ui_routes"],
        "api_contracts": flow["api_contracts"],
        "tests": flow["tests"],
    }


def _missing_paths(paths_value: object) -> list[str]:
    """Return path checks that are absent from the repository."""

    paths = _as_string_list(paths_value)
    return [path for path in paths if not (PROJECT_ROOT / path).exists()]


def _missing_api_contracts(contracts_value: object, files_value: object) -> list[str]:
    """Return API contracts that are not visible in the declared route files."""

    contracts = _as_string_list(contracts_value)
    files = _as_string_list(files_value)
    route_source = "\n".join((PROJECT_ROOT / path).read_text(encoding="utf-8") for path in files if (PROJECT_ROOT / path).exists())
    missing: list[str] = []
    for contract in contracts:
        route_fragment = contract.split(" ", 1)[-1]
        if route_fragment not in route_source:
            missing.append(contract)
    return missing


def _as_string_list(value: object) -> list[str]:
    """Normalize a matrix value into a string list."""

    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def main() -> int:
    """CLI entrypoint."""

    report = run_gate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["readiness_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
