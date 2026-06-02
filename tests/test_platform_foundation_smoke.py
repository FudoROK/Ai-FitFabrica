"""Tests for the portable platform foundation smoke script."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _env() -> dict[str, str]:
    """Return an isolated environment with minimal portable baseline settings."""
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(("POSTGRES_", "REDIS_", "OBJECT_STORAGE_", "QDRANT_", "VERTEX_")):
            env.pop(key)
    env.update(
        {
            "ENVIRONMENT": "test",
            "MESSAGING_PROVIDER": "none",
            "GCP_PROJECT_ID": "test-project",
            "PUBSUB_TOPIC_NAME": "agent-jobs",
            "LLM_PROVIDER": "fake",
            "MEMORY_SUMMARY_ENABLED": "false",
        }
    )
    return env


def test_platform_foundation_smoke_reports_portable_runtime_configuration() -> None:
    """The smoke script must report portable runtime settings without touching infrastructure."""
    result = subprocess.run(
        [sys.executable, "scripts/platform_foundation_smoke.py"],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )

    assert result.returncode == 0
    assert "platform_foundation_smoke" in result.stdout
    assert "readiness_status=blocked" in result.stdout
    assert "object_storage_backend=in_memory" in result.stdout
    assert "qdrant_backend=qdrant" in result.stdout
    assert "operations_queue_backend=in_memory" in result.stdout
    assert "operations_worker_name=portable-worker" in result.stdout


def test_platform_foundation_smoke_accepts_portable_env_file_and_can_gate_readiness(tmp_path: Path) -> None:
    """The smoke script should validate a filled portable env file through generic aliases."""
    env_file = tmp_path / "portable.env"
    env_file.write_text(
        "\n".join(
            [
                "ENVIRONMENT=staging",
                "MESSAGING_PROVIDER=none",
                "PROJECT_ID=portable-project",
                "EVENT_TOPIC_NAME=portable-events",
                "MEMORY_SUMMARY_ENABLED=false",
                "LLM_PROVIDER=fake",
                "POSTGRES_DSN=postgresql+asyncpg://fitfabrica:pass@postgres:5432/fitfabrica",
                "REDIS_URL=redis://redis:6379/0",
                "OBJECT_STORAGE_BACKEND=s3",
                "OBJECT_STORAGE_BUCKET_NAME=fitfabrica-staging",
                "OBJECT_STORAGE_REGION=auto",
                "OBJECT_STORAGE_ENDPOINT_URL=http://minio:9000",
                "OBJECT_STORAGE_ACCESS_KEY_ID=minioadmin",
                "OBJECT_STORAGE_SECRET_ACCESS_KEY=minioadmin123",
                "QDRANT_URL=http://qdrant:6333",
                "OPERATIONS_QUEUE_BACKEND=redis",
                "PUBLIC_STATUS_ENDPOINTS_ENABLED=true",
                "STATUS_ENDPOINT_TOKEN=portable-status-token",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/platform_foundation_smoke.py", "--env-file", str(env_file), "--require-ready"],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )

    assert result.returncode == 0
    assert "readiness_status=ready" in result.stdout
    assert "project_id=portable-project" in result.stdout
    assert "event_topic_name=portable-events" in result.stdout
