"""Validate that the current host can start the portable Docker contour."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    """Captured result of one host prerequisite command."""

    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class PreflightReport:
    """Structured portable infrastructure readiness result."""

    readiness_status: str
    failed_checks: tuple[str, ...]
    blocker: str | None


def evaluate_preflight(
    *,
    docker_cli_available: bool,
    docker_info: CommandResult | None,
    compose_config: CommandResult | None,
) -> PreflightReport:
    """Evaluate host command results without performing side effects."""
    if not docker_cli_available:
        return PreflightReport("blocked", ("docker_cli",), "docker_cli_unavailable")
    if docker_info is None or docker_info.returncode != 0:
        diagnostic = "" if docker_info is None else f"{docker_info.stdout}\n{docker_info.stderr}".lower()
        blocker = (
            "hardware_virtualization_unavailable"
            if '"hasnovirtualization":true' in diagnostic.replace(" ", "")
            else "docker_engine_unavailable"
        )
        return PreflightReport("blocked", ("docker_engine",), blocker)
    if compose_config is None or compose_config.returncode != 0:
        return PreflightReport("blocked", ("compose_config",), "compose_config_invalid")
    return PreflightReport("ready", (), None)


def _run(command: list[str]) -> CommandResult:
    """Run one prerequisite command and capture its output."""
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _docker_diagnostic_text(result: CommandResult) -> CommandResult:
    """Append Docker Desktop diagnostics when the engine is unavailable."""
    log_path = Path.home() / "AppData/Local/Docker/log/host/com.docker.backend.exe.log"
    if result.returncode == 0 or not log_path.exists():
        return result
    try:
        log_tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-200:])
    except OSError:
        return result
    return CommandResult(result.returncode, result.stdout, f"{result.stderr}\n{log_tail}")


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Check host readiness for portable Docker infrastructure.")
    parser.add_argument(
        "--compose-file",
        type=Path,
        default=Path("docker-compose.portable-staging.yml"),
        help="Compose file to validate.",
    )
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero when the host is blocked.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the host preflight and print a structured JSON report."""
    args = _parser().parse_args(argv)
    docker_available = shutil.which("docker") is not None
    docker_info = _docker_diagnostic_text(_run(["docker", "info"])) if docker_available else None
    compose_config = None
    if docker_info is not None and docker_info.returncode == 0:
        compose_config = _run(["docker", "compose", "-f", str(args.compose_file), "config", "--quiet"])
    report = evaluate_preflight(
        docker_cli_available=docker_available,
        docker_info=docker_info,
        compose_config=compose_config,
    )
    print(json.dumps(asdict(report), sort_keys=True))
    return 2 if args.require_ready and report.readiness_status != "ready" else 0


if __name__ == "__main__":
    raise SystemExit(main())
