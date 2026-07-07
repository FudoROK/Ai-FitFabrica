"""Run the local no-billing acceptance gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "apps" / "web"


@dataclass(frozen=True)
class GateCommand:
    """One local acceptance command."""

    name: str
    command: tuple[str, ...]
    cwd: str


Runner = Callable[[GateCommand], subprocess.CompletedProcess[str]]


def _python_executable() -> str:
    """Return the current Python executable for portable local gate commands."""

    return sys.executable


def _npm_executable() -> str:
    """Return the npm executable name for the current OS."""

    return "npm.cmd" if os.name == "nt" else "npm"


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Run no-billing local acceptance checks.")
    parser.add_argument("--list", action="store_true", help="Print command matrix without running checks.")
    parser.add_argument("--skip-frontend-build", action="store_true", help="Skip npm run build for a faster pass.")
    parser.add_argument("--full-backend", action="store_true", help="Include full backend pytest suite.")
    return parser


def _command_matrix(*, include_frontend_build: bool, include_full_backend: bool) -> list[GateCommand]:
    """Return the no-billing local acceptance command matrix."""

    python = _python_executable()
    commands = [
        GateCommand(
            name="backend_no_billing_guardrails",
            command=(
                python,
                "-m",
                "pytest",
                "tests/test_status_routes_health_runtime.py",
                "tests/test_runtime_security.py",
                "tests/test_public_request_routes.py",
                "tests/test_public_frontend_routes.py",
                "tests/test_no_billing_frontend_guardrails.py",
                "tests/test_workspace_text_encoding.py",
                "tests/test_frontend_route_documentation.py",
                "tests/test_admin_readiness_page.py",
                "tests/test_admin_business_catalog_page.py",
                "tests/test_admin_business_accounts_page.py",
                "tests/test_admin_taxonomy_page.py",
                "tests/test_post_billing_acceptance_gate.py",
                "tests/test_no_billing_acceptance_gate.py",
                "tests/test_auth_readiness_gate.py",
                "tests/test_billing_readiness_gate.py",
                "tests/test_client_readiness_gate.py",
                "tests/test_production_fallback_usage_audit.py",
                "tests/test_web_dependency_audit.py",
                "tests/test_owner_status_docs.py",
                "tests/test_staging_no_billing_smoke_script.py",
                "-q",
            ),
            cwd=".",
        ),
        GateCommand(
            name="post_billing_artifact_gate",
            command=(python, "scripts/post_billing_acceptance_gate.py"),
            cwd=".",
        ),
        GateCommand(
            name="client_readiness_gate",
            command=(python, "scripts/client_readiness_gate.py"),
            cwd=".",
        ),
        GateCommand(
            name="auth_readiness_gate",
            command=(python, "scripts/auth_readiness_gate.py"),
            cwd=".",
        ),
        GateCommand(
            name="billing_readiness_gate",
            command=(python, "scripts/billing_readiness_gate.py"),
            cwd=".",
        ),
        GateCommand(
            name="architecture_guardrail",
            command=(python, "scripts/check_architecture.py"),
            cwd=".",
        ),
        GateCommand(
            name="production_fallback_usage_audit",
            command=(python, "scripts/production_fallback_usage_audit.py", "--require-ready"),
            cwd=".",
        ),
        GateCommand(
            name="web_dependency_audit",
            command=(python, "scripts/web_dependency_audit.py", "--require-ready"),
            cwd=".",
        ),
        GateCommand(
            name="python_compileall",
            command=(python, "-m", "compileall", "-q", "src", "scripts", "tests"),
            cwd=".",
        ),
        GateCommand(name="web_typecheck", command=(_npm_executable(), "run", "typecheck"), cwd="apps/web"),
        GateCommand(name="web_lint", command=(_npm_executable(), "run", "lint"), cwd="apps/web"),
    ]
    if include_frontend_build:
        commands.append(GateCommand(name="web_build", command=(_npm_executable(), "run", "build"), cwd="apps/web"))
    if include_full_backend:
        commands.append(GateCommand(name="full_backend_pytest", command=(python, "-m", "pytest", "-q"), cwd="."))
    return commands


def _default_runner(command: GateCommand) -> subprocess.CompletedProcess[str]:
    """Run one gate command and capture output."""

    cwd = PROJECT_ROOT if command.cwd == "." else PROJECT_ROOT / command.cwd
    try:
        return subprocess.run(
            list(command.command),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(
            args=list(command.command),
            returncode=127,
            stdout="",
            stderr=f"executable_not_found: {exc}",
        )


def run_gate(*, commands: list[GateCommand], runner: Runner = _default_runner) -> dict[str, object]:
    """Run all commands and return a machine-readable report."""

    results: dict[str, dict[str, object]] = {}
    failed_checks: list[str] = []
    for command in commands:
        result = runner(command)
        status = "passed" if result.returncode == 0 else "failed"
        if status == "failed":
            failed_checks.append(command.name)
        results[command.name] = {
            "status": status,
            "returncode": result.returncode,
            "cwd": command.cwd,
            "command": list(command.command),
            "stdout_tail": _tail(result.stdout),
            "stderr_tail": _tail(result.stderr),
        }
    return {
        "gate": "no_billing_local_acceptance",
        "readiness_status": "blocked" if failed_checks else "ready",
        "failed_checks": failed_checks,
        "checks": results,
    }


def _tail(value: str, *, limit: int = 4000) -> str:
    """Keep command output bounded in JSON reports."""

    if len(value) <= limit:
        return value
    return value[-limit:]


def _command_list_payload(commands: list[GateCommand]) -> dict[str, object]:
    """Return a JSON-safe command list."""

    return {
        "gate": "no_billing_local_acceptance",
        "commands": [
            {
                "name": command.name,
                "cwd": command.cwd,
                "command": list(command.command),
            }
            for command in commands
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    args = _parser().parse_args(argv)
    commands = _command_matrix(
        include_frontend_build=not args.skip_frontend_build,
        include_full_backend=args.full_backend,
    )
    if args.list:
        print(json.dumps(_command_list_payload(commands), ensure_ascii=False, sort_keys=True))
        return 0
    report = run_gate(commands=commands)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["readiness_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
