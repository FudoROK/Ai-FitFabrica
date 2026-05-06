from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_infra_storage_modules_do_not_embed_domain_patch_canonicalization() -> None:
    guarded_modules = (
        "src/adapters/database/firestore/storage_primitives.py",
        "src/adapters/database/firestore/lead_store.py",
        "src/adapters/database/firestore/firestore_client_factory.py",
        "src/adapters/database/firestore/message_store.py",
        "src/adapters/database/firestore/summary_store.py",
        "src/adapters/database/firestore/crm_binding_store.py",
    )
    forbidden_tokens = (
        "compose_lead_update_payload",
        "canonicalize_lead_patch",
        "extract_raw_lead_patch",
    )

    for module in guarded_modules:
        text = _read(module)
        for token in forbidden_tokens:
            assert token not in text


def test_event_state_machine_remains_canonical_processing_owner() -> None:
    event_state_machine_text = _read("src/adapters/database/firestore/event_state_machine.py")

    assert "start_normalized_event_processing" in event_state_machine_text


def test_single_final_canonicalization_point_is_repository_only() -> None:
    ingest_text = _read("src/use_cases/lead/ingest_lead_patch_use_case.py")
    repo_text = _read("src/adapters/database/firestore/firestore_repositories.py")

    assert "compose_lead_update_payload" not in ingest_text
    assert "patch_preparation_service.compose(" in repo_text


def test_firestore_repositories_has_no_legacy_monkeypatch_hooks() -> None:
    repo_text = _read("src/adapters/database/firestore/firestore_repositories.py")

    assert "get_lead_by_id =" not in repo_text
    assert "apply_lead_patch =" not in repo_text
    assert "compatibility hooks" not in repo_text


def test_firestore_repositories_public_surface_includes_runtime_facade() -> None:
    repo_text = _read("src/adapters/database/firestore/firestore_repositories.py")

    assert "class FirestoreLeadRepository" in repo_text
    assert "class FirestoreSessionRepository" in repo_text
