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
        "run --rm --no-deps api python scripts/platform_foundation_smoke.py --require-ready",
        "python scripts/business_catalog_search_index_readiness.py --require-db",
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
    assert 'build api' in deploy_script
    assert 'build api worker' not in deploy_script
    assert 'run --rm --no-deps api' in deploy_script
    assert 'python scripts/platform_foundation_smoke.py --require-ready' in deploy_script
    assert 'python scripts/business_catalog_search_index_readiness.py --require-db' in deploy_script
    assert "docker compose -f" in deploy_script
    assert "reverse_proxy 127.0.0.1:8080" in caddy_example


def test_portable_remote_ubuntu_runbook_exists() -> None:
    source = Path("docs/runbooks/portable_remote_staging_ubuntu_22_04.md").read_text(encoding="utf-8")

    required_fragments = [
        "Ubuntu `22.04 LTS`",
        "ssh ubuntu@<server-ip>",
        "sudo bash scripts/bootstrap_portable_host.sh",
        "run --rm --no-deps api python scripts/platform_foundation_smoke.py --require-ready",
        "bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local",
        "docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local ps",
        "MESSAGING_PROVIDER=none",
    ]

    for fragment in required_fragments:
        assert fragment in source


def test_portable_shell_scripts_use_linux_line_endings() -> None:
    """Keep deployment scripts directly executable on the Linux staging host."""
    for path in Path("scripts").glob("*.sh"):
        assert b"\r\n" not in path.read_bytes(), f"{path} must use LF line endings"


def test_portable_smoke_script_is_available_inside_the_api_image() -> None:
    """Allow the deployment readiness gate to run inside the built API image."""
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert "scripts/*" in dockerignore
    assert "!scripts/platform_foundation_smoke.py" in dockerignore
    assert "!scripts/business_catalog_search_index_readiness.py" in dockerignore
    assert "!scripts/reindex_business_catalog_search.py" in dockerignore
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert "scripts/business_catalog_search_index_readiness.py" in dockerfile
    assert "scripts/reindex_business_catalog_search.py" in dockerfile


def test_backend_deploy_archive_script_excludes_local_env_and_secret_files() -> None:
    """Prevent staging deploy archives from overwriting VM-only env files."""

    script = Path("scripts/create_backend_deploy_archive.ps1").read_text(encoding="utf-8")

    required_excludes = [
        "--exclude=.env",
        "--exclude=.env.*",
        "--exclude=apps/web/.env.local",
        "--exclude=service-account.json",
        "--exclude=secrets",
        "--exclude=*.pem",
        "--exclude=*.key",
        "--exclude=*.p12",
    ]
    for fragment in required_excludes:
        assert fragment in script
    assert "Deployment archive contains local env or secret files." in script
