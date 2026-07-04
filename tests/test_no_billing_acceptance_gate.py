"""Tests for the no-billing local acceptance gate."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from scripts import no_billing_acceptance_gate as gate


def test_no_billing_gate_command_matrix_covers_backend_frontend_and_readiness() -> None:
    commands = gate._command_matrix(include_frontend_build=True, include_full_backend=False)
    names = {command.name for command in commands}
    backend_command = next(command for command in commands if command.name == "backend_no_billing_guardrails")

    assert "backend_no_billing_guardrails" in names
    assert "client_readiness_gate" in names
    assert "post_billing_artifact_gate" in names
    assert "architecture_guardrail" in names
    assert "python_compileall" in names
    assert "web_typecheck" in names
    assert "web_lint" in names
    assert "web_build" in names
    assert "full_backend_pytest" not in names
    assert "tests/test_client_readiness_gate.py" in backend_command.command
    assert "tests/test_staging_no_billing_smoke_script.py" in backend_command.command


def test_no_billing_gate_can_include_full_backend_suite() -> None:
    commands = gate._command_matrix(include_frontend_build=False, include_full_backend=True)
    names = {command.name for command in commands}

    assert "web_build" not in names
    assert "full_backend_pytest" in names


def test_no_billing_gate_run_report_marks_failed_command() -> None:
    def _runner(command: gate.GateCommand) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command.command,
            returncode=1 if command.name == "web_lint" else 0,
            stdout="ok",
            stderr="lint failed" if command.name == "web_lint" else "",
        )

    report = gate.run_gate(
        commands=[
            gate.GateCommand(name="backend_no_billing_guardrails", command=("python", "-m", "pytest"), cwd="."),
            gate.GateCommand(name="web_lint", command=("npm", "run", "lint"), cwd="apps/web"),
        ],
        runner=_runner,
    )

    assert report["readiness_status"] == "blocked"
    assert report["failed_checks"] == ["web_lint"]


def test_no_billing_gate_cli_lists_commands_without_running_them() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/no_billing_acceptance_gate.py", "--list"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["gate"] == "no_billing_local_acceptance"
    assert any(command["name"] == "web_typecheck" for command in payload["commands"])


def test_no_billing_gate_uses_windows_npm_command() -> None:
    if os.name == "nt":
        assert gate._npm_executable() == "npm.cmd"


def test_default_runner_reports_missing_executable_without_traceback() -> None:
    result = gate._default_runner(
        gate.GateCommand(name="missing", command=("definitely-not-a-real-command-fitfabrica",), cwd=".")
    )

    assert result.returncode == 127
    assert "executable_not_found" in result.stderr
