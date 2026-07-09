"""Tests for the portable infrastructure host preflight."""

from __future__ import annotations

from scripts.portable_infrastructure_preflight import CommandResult, evaluate_preflight


def test_preflight_is_ready_when_docker_engine_and_compose_are_available() -> None:
    """A healthy Docker host should be accepted for portable infrastructure."""
    report = evaluate_preflight(
        docker_cli_available=True,
        docker_info=CommandResult(returncode=0, stdout="Docker Desktop", stderr=""),
        compose_config=CommandResult(returncode=0, stdout="services: {}", stderr=""),
    )

    assert report.readiness_status == "ready"
    assert report.failed_checks == ()


def test_preflight_reports_virtualization_root_cause_from_docker_error() -> None:
    """A stopped engine with disabled virtualization should expose the actionable blocker."""
    report = evaluate_preflight(
        docker_cli_available=True,
        docker_info=CommandResult(
            returncode=1,
            stdout="",
            stderr='backend state: {"hasNoVirtualization":true,"state":"stopped"}',
        ),
        compose_config=None,
    )

    assert report.readiness_status == "blocked"
    assert report.failed_checks == ("docker_engine",)
    assert report.blocker == "hardware_virtualization_unavailable"


def test_preflight_reports_missing_docker_cli() -> None:
    """A host without Docker CLI should fail before compose validation."""
    report = evaluate_preflight(
        docker_cli_available=False,
        docker_info=None,
        compose_config=None,
    )

    assert report.readiness_status == "blocked"
    assert report.failed_checks == ("docker_cli",)
    assert report.blocker == "docker_cli_unavailable"
