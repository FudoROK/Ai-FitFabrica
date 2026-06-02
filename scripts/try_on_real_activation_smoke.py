"""Dry-run smoke check for real Vertex Try-On activation readiness."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.settings import Settings, load_settings, validate_settings
from src.use_cases.try_on.activation_probe import probe_try_on_real_activation


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser for readiness gating."""
    parser = argparse.ArgumentParser(description="Try-On real activation readiness smoke check.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless readiness_status is ready.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Load settings from the provided env file instead of the current process environment.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Print the real Try-On activation readiness surface without touching live services."""
    args = _parser().parse_args(argv)
    print("try_on_real_activation_smoke")
    try:
        settings = _load_smoke_settings(env_file=args.env_file)
    except ValueError as exc:
        print("readiness_status=blocked")
        print(f"error={exc}")
        return 1

    result = probe_try_on_real_activation(settings)
    print(f"backend={result.backend}")
    print(f"activation_enabled={str(result.activation_enabled).lower()}")
    print(f"readiness_status={result.readiness_status}")
    print(f"fallback_backend={result.fallback_backend}")
    for check in result.checks:
        print(f"check:{check.name}={check.status}:{check.message}")
    if result.readiness_status == "blocked":
        return 1
    if args.require_ready and result.readiness_status != "ready":
        print("error=readiness gate requires readiness_status=ready")
        return 2
    return 0


def _load_smoke_settings(*, env_file: Path | None):
    """Load validated settings either from process env or from one explicit env file."""
    if env_file is None:
        return load_settings()
    settings = Settings(_env_file=str(env_file), _env_file_encoding="utf-8")
    validate_settings(settings)
    return settings


if __name__ == "__main__":
    raise SystemExit(main())
