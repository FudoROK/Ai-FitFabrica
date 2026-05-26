"""Manual smoke check for Try-On durable storage settings.

Default mode is dry-run and never writes to GCS or Firestore. Live writes require
both --live-write-check and --confirm-live-write, and must only be run after the
human has approved real cloud activation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.settings import load_settings


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Try-On durable storage smoke check.")
    parser.add_argument("--live-write-check", action="store_true", help="Run a real storage write check.")
    parser.add_argument(
        "--confirm-live-write",
        action="store_true",
        help="Confirm that live cloud writes were explicitly approved.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a dry-run settings check or reject unsafe live execution."""
    args = _parser().parse_args(argv)
    if args.live_write_check and not args.confirm_live_write:
        print("--confirm-live-write is required with --live-write-check", file=sys.stderr)
        return 2

    settings = load_settings()
    print("try_on_storage_smoke")
    print(f"dry_run={str(not args.live_write_check).lower()}")
    print(f"live_write_check={str(args.live_write_check).lower()}")
    print(f"try_on_file_storage_backend={settings.try_on_file_storage_backend}")
    print(f"try_on_job_repository_backend={settings.try_on_job_repository_backend}")
    print(f"try_on_gcs_bucket_configured={str(settings.try_on_gcs_bucket_name is not None).lower()}")
    print(f"try_on_firestore_collection={settings.try_on_firestore_collection}")

    if not args.live_write_check:
        print("No GCS or Firestore write was attempted.")
        return 0

    print("Live write check is intentionally not implemented in this activation gate.")
    print("Create a separate approved plan before writing probe objects/documents.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
