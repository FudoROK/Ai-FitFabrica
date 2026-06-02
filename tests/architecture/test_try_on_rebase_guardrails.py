from __future__ import annotations

from pathlib import Path


def test_active_try_on_runtime_paths_do_not_select_firestore_or_gcs() -> None:
    routes_text = Path("src/entrypoints/try_on_routes.py").read_text(encoding="utf-8")
    runtime_text = Path("src/entrypoints/runtime_dependencies.py").read_text(encoding="utf-8")

    assert "FirestoreTryOnJobRepository(" not in routes_text
    assert "GcsTryOnFileStorage(" not in routes_text
    assert "FirestoreTryOnJobRepository(" not in runtime_text
