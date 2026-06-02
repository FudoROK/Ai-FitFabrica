"""Dry-run smoke check for portable platform foundation settings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.settings import Settings, load_settings, validate_settings


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser for portable deployment readiness checks."""
    parser = argparse.ArgumentParser(description="Portable platform foundation smoke check.")
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Load settings from the provided env file instead of the current process environment.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless readiness_status is ready.",
    )
    return parser


def _is_placeholder(value: str | None) -> bool:
    """Return True when a configuration value is still an obvious placeholder."""
    normalized = (value or "").strip().lower()
    if not normalized:
        return True
    return normalized.startswith(("replace-with", "replace_me", "your-", "tbd", "<")) or normalized.endswith(">")


def _load_smoke_settings(*, env_file: Path | None) -> Settings:
    """Load validated settings either from the current process env or one explicit env file."""
    if env_file is None:
        return load_settings()
    env_values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_values[key.strip()] = value.strip()
    settings = Settings(_env_file=None, **env_values)
    validate_settings(settings)
    return settings


def main(argv: list[str] | None = None) -> int:
    """Print the portable deployment readiness surface without touching live services."""
    args = _parser().parse_args(argv)
    print("platform_foundation_smoke")
    try:
        settings = _load_smoke_settings(env_file=args.env_file)
    except ValueError as exc:
        print("readiness_status=blocked")
        print(f"error={exc}")
        return 1

    readiness_errors: list[str] = []
    if not (settings.postgres_dsn or "").strip() or _is_placeholder(settings.postgres_dsn):
        readiness_errors.append("postgres_dsn")
    if not (settings.redis_url or "").strip() or _is_placeholder(settings.redis_url):
        readiness_errors.append("redis_url")
    if settings.object_storage_backend != "s3":
        readiness_errors.append("object_storage_backend")
    if not (settings.object_storage_bucket_name or "").strip() or _is_placeholder(settings.object_storage_bucket_name):
        readiness_errors.append("object_storage_bucket_name")
    if not (settings.object_storage_endpoint_url or "").strip() or _is_placeholder(settings.object_storage_endpoint_url):
        readiness_errors.append("object_storage_endpoint_url")
    if not (settings.object_storage_access_key_id or "").strip() or _is_placeholder(settings.object_storage_access_key_id):
        readiness_errors.append("object_storage_access_key_id")
    if not (
        settings.object_storage_secret_access_key or ""
    ).strip() or _is_placeholder(settings.object_storage_secret_access_key):
        readiness_errors.append("object_storage_secret_access_key")
    if not (settings.qdrant_url or "").strip() or _is_placeholder(settings.qdrant_url):
        readiness_errors.append("qdrant_url")
    if settings.operations_queue_backend != "redis":
        readiness_errors.append("operations_queue_backend")
    if settings.public_status_endpoints_enabled and (
        not (settings.status_endpoint_token or "").strip() or _is_placeholder(settings.status_endpoint_token)
    ):
        readiness_errors.append("status_endpoint_token")

    readiness_status = "ready" if not readiness_errors else "blocked"
    print(f"readiness_status={readiness_status}")
    print(f"postgres_configured={str(bool(settings.postgres_dsn)).lower()}")
    print(f"redis_configured={str(bool(settings.redis_url)).lower()}")
    print(f"object_storage_backend={settings.object_storage_backend}")
    print(f"qdrant_backend={settings.vector_backend}")
    print(f"qdrant_configured={str(bool(settings.qdrant_url)).lower()}")
    print(f"operations_queue_backend={settings.operations_queue_backend}")
    print(f"operations_worker_name={settings.operations_worker_name}")
    print(f"project_id={settings.gcp_project_id}")
    print(f"event_topic_name={settings.pubsub_topic_name}")
    if readiness_errors:
        for error in readiness_errors:
            print(f"check:{error}=blocked")
    if args.require_ready and readiness_status != "ready":
        print("error=readiness gate requires readiness_status=ready")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
