from __future__ import annotations

from pathlib import Path


def test_active_try_on_runtime_paths_do_not_select_firestore_or_gcs() -> None:
    routes_text = Path("src/entrypoints/try_on_routes.py").read_text(encoding="utf-8")
    runtime_text = Path("src/entrypoints/runtime_dependencies.py").read_text(encoding="utf-8")

    assert "FirestoreTryOnJobRepository(" not in routes_text
    assert "GcsTryOnFileStorage(" not in routes_text
    assert "FirestoreTryOnJobRepository(" not in runtime_text


def test_try_on_legacy_firestore_and_gcs_adapters_are_removed_from_active_tree() -> None:
    assert not Path("src/adapters/try_on/firestore_repository.py").exists()
    assert not Path("src/adapters/try_on/gcs_file_storage.py").exists()


def test_try_on_domain_and_settings_do_not_expose_firestore_or_gcs_storage_backends() -> None:
    domain_text = Path("src/domain/try_on.py").read_text(encoding="utf-8")
    settings_text = Path("src/settings_model_try_on.py").read_text(encoding="utf-8")

    assert '"gcs"' not in domain_text
    assert '"firestore"' not in settings_text
    assert "try_on_job_repository_backend" not in settings_text
    assert "try_on_firestore_collection" not in settings_text


def test_try_on_analysis_bundle_stays_provider_neutral() -> None:
    """Keep mandatory analysis orchestration independent from provider SDKs."""
    text = Path("src/use_cases/try_on/analysis_bundle_service.py").read_text(encoding="utf-8")

    assert "google.genai" not in text
    assert "vertexai" not in text
    assert "src.adk_agents" not in text
