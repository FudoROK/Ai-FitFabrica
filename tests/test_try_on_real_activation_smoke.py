"""Tests for the real Try-On activation dry-run smoke script."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _env() -> dict[str, str]:
    """Return an isolated environment with required settings for the smoke script."""
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(("TRY_ON_", "VERTEX_", "POSTGRES_", "REDIS_", "OBJECT_STORAGE_")):
            env.pop(key)
    env.update(
        {
            "ENVIRONMENT": "test",
            "GCP_PROJECT_ID": "test-project",
            "PUBSUB_TOPIC_NAME": "agent-jobs",
            "LLM_PROVIDER": "fake",
            "MEMORY_SUMMARY_ENABLED": "false",
        }
    )
    return env


def test_try_on_real_activation_smoke_reports_inactive_state() -> None:
    """The smoke script must report inactive status when the real path is not requested."""
    result = subprocess.run(
        [sys.executable, "scripts/try_on_real_activation_smoke.py"],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )

    assert result.returncode == 0
    assert "try_on_real_activation_smoke" in result.stdout
    assert "readiness_status=inactive" in result.stdout


def test_try_on_real_activation_smoke_blocks_invalid_real_config() -> None:
    """The smoke script must fail when the real path is requested with blocked readiness."""
    env = _env()
    env.update(
        {
            "TRY_ON_GENERATION_BACKEND": "vertex_virtual_try_on",
            "ENABLE_REAL_TRY_ON_GENERATION": "true",
            "VERTEX_PROJECT": "fitfabrica-test",
        }
    )
    result = subprocess.run(
        [sys.executable, "scripts/try_on_real_activation_smoke.py"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 1
    assert "readiness_status=blocked" in result.stdout


def test_try_on_real_activation_smoke_require_ready_rejects_inactive_state() -> None:
    """The smoke script must reject inactive status when the operator asks for a ready gate."""
    result = subprocess.run(
        [sys.executable, "scripts/try_on_real_activation_smoke.py", "--require-ready"],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )

    assert result.returncode == 2
    assert "readiness_status=inactive" in result.stdout
    assert "readiness gate requires readiness_status=ready" in result.stdout


def test_try_on_real_activation_smoke_can_load_explicit_env_file(tmp_path: Path) -> None:
    """The smoke script must support validating one explicit env pack file."""
    env_file = tmp_path / "staging.env"
    env_file.write_text(
        "\n".join(
            [
                "ENVIRONMENT=test",
                "GCP_PROJECT_ID=test-project",
                "PUBSUB_TOPIC_NAME=agent-jobs",
                "LLM_PROVIDER=fake",
                "MEMORY_SUMMARY_ENABLED=false",
            ]
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "scripts/try_on_real_activation_smoke.py", "--env-file", str(env_file)],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )

    assert result.returncode == 0
    assert "readiness_status=inactive" in result.stdout
