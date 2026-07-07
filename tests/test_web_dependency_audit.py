"""Tests for the web dependency audit gate."""

from __future__ import annotations

import json
import subprocess

from scripts import web_dependency_audit as audit


def _completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    """Build a completed process for audit runner tests."""

    return subprocess.CompletedProcess(args=("npm", "audit"), returncode=returncode, stdout=stdout, stderr="")


def test_web_dependency_audit_allows_low_and_moderate_findings_as_evidence() -> None:
    """Low and moderate findings are reported but do not block pre-billing readiness."""

    payload = {
        "metadata": {
            "vulnerabilities": {
                "info": 0,
                "low": 1,
                "moderate": 2,
                "high": 0,
                "critical": 0,
                "total": 3,
            }
        }
    }

    report = audit.run_audit(runner=lambda: _completed(json.dumps(payload)))

    assert report["gate"] == "web_dependency_audit"
    assert report["readiness_status"] == "ready"
    assert report["failed_checks"] == []
    assert report["checks"]["npm_audit"]["vulnerabilities"]["moderate"] == 2


def test_web_dependency_audit_blocks_high_or_critical_findings() -> None:
    """High or critical findings block paid workflow acceptance."""

    payload = {
        "metadata": {
            "vulnerabilities": {
                "info": 0,
                "low": 0,
                "moderate": 0,
                "high": 1,
                "critical": 1,
                "total": 2,
            }
        }
    }

    report = audit.run_audit(runner=lambda: _completed(json.dumps(payload), returncode=1))

    assert report["readiness_status"] == "blocked"
    assert report["failed_checks"] == ["npm_audit"]
    assert report["checks"]["npm_audit"]["blocking_vulnerabilities"] == 2


def test_web_dependency_audit_blocks_unparseable_npm_output() -> None:
    """The gate fails closed when npm audit cannot return structured evidence."""

    report = audit.run_audit(runner=lambda: _completed("not json", returncode=1))

    assert report["readiness_status"] == "blocked"
    assert report["checks"]["npm_audit"]["reason"] == "invalid_npm_audit_json"
