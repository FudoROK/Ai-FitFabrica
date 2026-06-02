"""Guardrails for portable object storage migration."""

from __future__ import annotations

from pathlib import Path


def test_portable_storage_packages_do_not_import_google_cloud_storage() -> None:
    """Portable storage layers must stay free of provider-specific Google SDK imports."""
    for relative_path in [
        "src/adapters/storage/contracts.py",
        "src/adapters/storage/in_memory_object_storage.py",
        "src/adapters/storage/media_storage.py",
        "src/adapters/storage/object_naming.py",
        "src/adapters/storage/s3_object_storage.py",
    ]:
        text = Path(relative_path).read_text(encoding="utf-8")
        assert "google.cloud.storage" not in text


def test_try_on_route_wiring_no_longer_selects_gcs_backend() -> None:
    """Try-On routes must not select GCS-specific storage adapters anymore."""
    text = Path("src/entrypoints/try_on_routes.py").read_text(encoding="utf-8")

    assert "try_on_file_storage_backend" not in text
    assert "GcsTryOnFileStorage" not in text
