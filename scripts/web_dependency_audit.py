"""Run npm dependency audit evidence for the web frontend."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "apps" / "web"

Runner = Callable[[], subprocess.CompletedProcess[str]]


def _npm_executable() -> str:
    """Return the npm executable name for the current OS."""

    return "npm.cmd" if os.name == "nt" else "npm"


def _default_runner() -> subprocess.CompletedProcess[str]:
    """Run npm audit from the web app root and capture structured output."""

    try:
        return subprocess.run(
            [_npm_executable(), "audit", "--audit-level=high", "--json"],
            cwd=WEB_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(
            args=(_npm_executable(), "audit", "--audit-level=high", "--json"),
            returncode=127,
            stdout="",
            stderr=f"executable_not_found: {exc}",
        )


def _empty_vulnerabilities() -> dict[str, int]:
    """Return a complete npm vulnerability summary shape."""

    return {
        "info": 0,
        "low": 0,
        "moderate": 0,
        "high": 0,
        "critical": 0,
        "total": 0,
    }


def _extract_vulnerabilities(payload: object) -> dict[str, int]:
    """Extract npm audit vulnerability counts from a parsed JSON payload."""

    counts = _empty_vulnerabilities()
    if not isinstance(payload, dict):
        return counts
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        return counts
    vulnerabilities = metadata.get("vulnerabilities")
    if not isinstance(vulnerabilities, dict):
        return counts
    for key in counts:
        value = vulnerabilities.get(key, 0)
        counts[key] = value if isinstance(value, int) else 0
    return counts


def run_audit(*, runner: Runner = _default_runner) -> dict[str, object]:
    """Run npm audit and return a machine-readable readiness report."""

    result = runner()
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "gate": "web_dependency_audit",
            "readiness_status": "blocked",
            "failed_checks": ["npm_audit"],
            "checks": {
                "npm_audit": {
                    "status": "failed",
                    "returncode": result.returncode,
                    "reason": "invalid_npm_audit_json",
                    "stderr_tail": _tail(result.stderr),
                }
            },
        }

    vulnerabilities = _extract_vulnerabilities(payload)
    blocking_vulnerabilities = vulnerabilities["high"] + vulnerabilities["critical"]
    command_failed_without_blockers = result.returncode != 0 and blocking_vulnerabilities == 0
    status = "failed" if blocking_vulnerabilities or command_failed_without_blockers else "passed"
    reason = None
    if blocking_vulnerabilities:
        reason = "high_or_critical_vulnerabilities"
    elif command_failed_without_blockers:
        reason = "npm_audit_command_failed"
    check: dict[str, object] = {
        "status": status,
        "returncode": result.returncode,
        "audit_level": "high",
        "blocking_vulnerabilities": blocking_vulnerabilities,
        "vulnerabilities": vulnerabilities,
    }
    if reason:
        check["reason"] = reason
    return {
        "gate": "web_dependency_audit",
        "readiness_status": "blocked" if status == "failed" else "ready",
        "failed_checks": ["npm_audit"] if status == "failed" else [],
        "checks": {"npm_audit": check},
    }


def _tail(value: str, *, limit: int = 4000) -> str:
    """Keep command output bounded in JSON reports."""

    if len(value) <= limit:
        return value
    return value[-limit:]


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Run web npm dependency audit evidence.")
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
