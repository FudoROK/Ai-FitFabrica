from __future__ import annotations

from pathlib import Path


def test_portable_remote_staging_env_example_exists() -> None:
    source = Path(".env.portable-remote-staging.example").read_text(encoding="utf-8")

    required_fragments = [
        "MESSAGING_PROVIDER=none",
        "PROJECT_ID=ai-fitfabrica",
        "EVENT_TOPIC_NAME=staging-agent-jobs",
        "POSTGRES_DSN=postgresql+asyncpg://fitfabrica:replace-with-password@postgres:5432/fitfabrica",
        "REDIS_URL=redis://redis:6379/0",
        "OBJECT_STORAGE_ENDPOINT_URL=http://minio:9000",
        "QDRANT_URL=http://qdrant:6333",
        "OPERATIONS_QUEUE_BACKEND=redis",
    ]

    for fragment in required_fragments:
        assert fragment in source


def test_portable_remote_staging_runbook_exists() -> None:
    source = Path("docs/runbooks/portable_remote_staging_vm.md").read_text(encoding="utf-8")

    required_fragments = [
        "Docker Engine",
        "docker-compose.portable-staging.yml",
        ".env.portable-remote-staging.local",
        "alembic upgrade head",
        "Try-On Activation Dry Run",
        "platform_foundation_smoke.py --env-file .env.portable-remote-staging.local --require-ready",
        "bootstrap_portable_host.sh",
        "deploy_portable_runtime.sh",
        "Caddyfile.portable.example",
        "portable_remote_staging_ubuntu_22_04.md",
    ]

    for fragment in required_fragments:
        assert fragment in source


def test_portable_remote_bootstrap_scripts_and_proxy_example_exist() -> None:
    bootstrap_script = Path("scripts/bootstrap_portable_host.sh").read_text(encoding="utf-8")
    deploy_script = Path("scripts/deploy_portable_runtime.sh").read_text(encoding="utf-8")
    caddy_example = Path("deploy/caddy/Caddyfile.portable.example").read_text(encoding="utf-8")

    assert "docker compose plugin" in bootstrap_script or "docker-compose-plugin" in bootstrap_script
    assert "python scripts/platform_foundation_smoke.py --env-file" in deploy_script
    assert "docker compose -f" in deploy_script
    assert "reverse_proxy 127.0.0.1:8080" in caddy_example


def test_portable_remote_ubuntu_runbook_exists() -> None:
    source = Path("docs/runbooks/portable_remote_staging_ubuntu_22_04.md").read_text(encoding="utf-8")

    required_fragments = [
        "Ubuntu `22.04 LTS`",
        "ssh ubuntu@<server-ip>",
        "sudo bash scripts/bootstrap_portable_host.sh",
        "python scripts/platform_foundation_smoke.py --env-file .env.portable-remote-staging.local --require-ready",
        "bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local",
        "docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local ps",
        "MESSAGING_PROVIDER=none",
    ]

    for fragment in required_fragments:
        assert fragment in source
