"""Tests for the Try-On durable storage smoke script."""
from __future__ import annotations

import os
import subprocess
import sys


def _env() -> dict[str, str]:
    """Return an isolated environment with required settings for the smoke script."""
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("TRY_ON_") or key.startswith("VERTEX_"):
            env.pop(key)
    env.update(
        {
            "ENVIRONMENT": "test",
            "GCP_PROJECT_ID": "test-project",
            "PUBSUB_TOPIC_NAME": "agent-jobs",
            "LLM_PROVIDER": "fake",
            "MEMORY_SUMMARY_ENABLED": "false",
            "OBJECT_STORAGE_BACKEND": "in_memory",
            "TRY_ON_JOB_REPOSITORY_BACKEND": "in_memory",
        }
    )
    return env


def test_try_on_storage_smoke_defaults_to_dry_run() -> None:
    """The smoke script must not touch live cloud resources unless explicitly requested."""
    result = subprocess.run(
        [sys.executable, "scripts/try_on_storage_smoke.py"],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )

    assert result.returncode == 0
    assert "dry_run=true" in result.stdout
    assert "live_write_check=false" in result.stdout
    assert "No object storage or PostgreSQL write was attempted." in result.stdout


def test_try_on_storage_smoke_requires_explicit_live_flag() -> None:
    """A live write check must require an explicit CLI flag."""
    result = subprocess.run(
        [sys.executable, "scripts/try_on_storage_smoke.py", "--live-write-check"],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )

    assert result.returncode == 2
    assert "--confirm-live-write" in result.stderr
