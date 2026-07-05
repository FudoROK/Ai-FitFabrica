"""Audit reviewed runtime fallback references before production testing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDITED_FILES: tuple[str, ...] = (
    "src/entrypoints/runtime_dependency_workflow_builders.py",
    "src/entrypoints/runtime_dependency_product_card_builder.py",
    "src/entrypoints/runtime_dependency_operations_builders.py",
    "src/entrypoints/runtime_dependency_foundation_builders.py",
    "src/entrypoints/public_request_routes.py",
    "src/entrypoints/admin_business_catalog_routes.py",
)

RISK_TOKENS: tuple[str, ...] = (
    "InMemory",
    "in_memory",
    "Fake",
    "sandbox_fake",
    "stub_image_editing",
    "stub",
)

REVIEWED_MAX_COUNTS: dict[str, dict[str, int]] = {
    "src/entrypoints/runtime_dependency_workflow_builders.py": {
        "InMemory": 18,
        "in_memory": 4,
        "Fake": 5,
        "sandbox_fake": 3,
        "stub_image_editing": 1,
        "stub": 1,
    },
    "src/entrypoints/runtime_dependency_product_card_builder.py": {
        "InMemory": 2,
        "in_memory": 1,
        "Fake": 2,
        "sandbox_fake": 0,
        "stub_image_editing": 0,
        "stub": 0,
    },
    "src/entrypoints/runtime_dependency_operations_builders.py": {
        "InMemory": 4,
        "in_memory": 2,
        "Fake": 0,
        "sandbox_fake": 0,
        "stub_image_editing": 0,
        "stub": 0,
    },
    "src/entrypoints/runtime_dependency_foundation_builders.py": {
        "InMemory": 10,
        "in_memory": 2,
        "Fake": 0,
        "sandbox_fake": 0,
        "stub_image_editing": 0,
        "stub": 0,
    },
    "src/entrypoints/public_request_routes.py": {
        "InMemory": 2,
        "in_memory": 0,
        "Fake": 0,
        "sandbox_fake": 0,
        "stub_image_editing": 0,
        "stub": 0,
    },
    "src/entrypoints/admin_business_catalog_routes.py": {
        "InMemory": 2,
        "in_memory": 0,
        "Fake": 0,
        "sandbox_fake": 0,
        "stub_image_editing": 0,
        "stub": 0,
    },
}


def load_audited_sources() -> dict[str, str]:
    """Load source text for the runtime files covered by the fallback audit."""

    return {relative_path: (PROJECT_ROOT / relative_path).read_text(encoding="utf-8") for relative_path in AUDITED_FILES}


def _count_tokens(source: str) -> dict[str, int]:
    """Count fallback-risk tokens in one source file."""

    return {token: source.count(token) for token in RISK_TOKENS}


def _unexpected_increases(relative_path: str, actual: dict[str, int]) -> dict[str, int]:
    """Return token increases compared with the reviewed maximum counts."""

    reviewed = REVIEWED_MAX_COUNTS[relative_path]
    return {
        token: actual[token] - reviewed[token]
        for token in RISK_TOKENS
        if actual[token] > reviewed[token]
    }


def run_audit(*, sources: dict[str, str] | None = None) -> dict[str, object]:
    """Run the production fallback usage audit."""

    source_map = sources if sources is not None else load_audited_sources()
    checks: dict[str, dict[str, object]] = {}
    failed_checks: list[str] = []

    for relative_path in AUDITED_FILES:
        source = source_map.get(relative_path, "")
        actual = _count_tokens(source)
        increases = _unexpected_increases(relative_path, actual)
        status = "failed" if increases else "passed"
        if increases:
            failed_checks.append(relative_path)
        checks[relative_path] = {
            "status": status,
            "actual_counts": actual,
            "reviewed_max_counts": REVIEWED_MAX_COUNTS[relative_path],
            "unexpected_increases": increases,
        }

    return {
        "gate": "production_fallback_usage_audit",
        "readiness_status": "blocked" if failed_checks else "ready",
        "failed_checks": failed_checks,
        "policy": (
            "Runtime fallback references are allowed only within reviewed counts. "
            "New in-memory, fake, sandbox, or stub references require explicit review."
        ),
        "checks": checks,
    }


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Audit reviewed runtime fallback references.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the audit is ready.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    args = _parser().parse_args(argv)
    report = run_audit()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if args.require_ready and report["readiness_status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
