"""Tests for runtime fallback usage audit guardrails."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts import production_fallback_usage_audit as audit


def test_current_runtime_fallback_usage_matches_reviewed_allowlist() -> None:
    """Current reviewed runtime fallback references remain within the allowlist."""

    report = audit.run_audit()

    assert report["gate"] == "production_fallback_usage_audit"
    assert report["readiness_status"] == "ready"
    assert report["failed_checks"] == []


def test_audit_blocks_new_runtime_fallback_reference() -> None:
    """Adding a new runtime in-memory fallback must require explicit review."""

    sources = audit.load_audited_sources()
    target = "src/entrypoints/runtime_dependency_workflow_builders.py"
    sources[target] = f"{sources[target]}\nInMemoryUnsafeProductionFallback\n"

    report = audit.run_audit(sources=sources)

    assert report["readiness_status"] == "blocked"
    assert target in report["failed_checks"]
    assert report["checks"][target]["unexpected_increases"]["InMemory"] == 1


def test_production_fallback_usage_audit_cli_prints_json() -> None:
    """The audit script is directly runnable by acceptance gates."""

    result = subprocess.run(
        [sys.executable, "scripts/production_fallback_usage_audit.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["gate"] == "production_fallback_usage_audit"
    assert report["readiness_status"] == "ready"
