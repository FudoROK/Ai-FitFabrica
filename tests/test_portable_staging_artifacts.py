from __future__ import annotations

from pathlib import Path


def test_portable_staging_compose_exists() -> None:
    source = Path("docker-compose.portable-staging.yml").read_text(encoding="utf-8")

    required_fragments = [
        "api:",
        "worker:",
        "postgres:",
        "redis:",
        "minio:",
        "qdrant:",
        "python -m src.worker",
    ]

    for fragment in required_fragments:
        assert fragment in source


def test_portable_staging_env_example_exists() -> None:
    source = Path(".env.portable-staging.example").read_text(encoding="utf-8")

    required_fragments = [
        "PROJECT_ID=ai-fitfabrica",
        "EVENT_TOPIC_NAME=staging-agent-jobs",
        "POSTGRES_DSN=postgresql+asyncpg://fitfabrica:fitfabrica@postgres:5432/fitfabrica",
        "REDIS_URL=redis://redis:6379/0",
        "OBJECT_STORAGE_ENDPOINT_URL=http://minio:9000",
        "QDRANT_URL=http://qdrant:6333",
        "OPERATIONS_QUEUE_BACKEND=redis",
    ]

    for fragment in required_fragments:
        assert fragment in source


def test_portable_staging_runbook_exists() -> None:
    source = Path("docs/runbooks/portable_staging_runtime.md").read_text(encoding="utf-8")

    required_fragments = [
        "docker-compose.portable-staging.yml",
        ".env.portable-staging.local",
        "docker compose -f docker-compose.portable-staging.yml",
        "alembic upgrade head",
        "MinIO",
        "portable_infrastructure_preflight.py --require-ready",
        "platform_foundation_smoke.py --env-file .env.portable-staging.local --require-ready",
    ]

    for fragment in required_fragments:
        assert fragment in source
