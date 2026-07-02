from __future__ import annotations

from pathlib import Path

from scripts.architecture_rules import REPO_ROOT, run_architecture_checks


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_import_boundary_rules_hold() -> None:
    violations = [v for v in run_architecture_checks() if v.rule in {
        "domain_import_boundary",
        "llm_core_boundary",
        "llm_provider_boundary",
        "llm_transport_boundary",
        "llm_transport_business_semantics",
        "use_case_concrete_adapter_import",
        "use_case_firestore_low_level_import",
        "use_case_vendor_import",
        "vendor_sdk_boundary",
        "forbidden_bridge_import",
        "scripts_forbidden_import",
        "identity_core_runtime_import_boundary",
        "identity_core_internal_leakage",
        "identity_contract_boundary_leakage",
        "identity_model_boundary_leakage",
    }]
    assert violations == []


def test_firestore_write_discipline_holds() -> None:
    violations = [v for v in run_architecture_checks() if v.rule == "firestore_write_discipline"]
    assert violations == []


def test_legacy_dialog_service_layer_is_removed() -> None:
    assert not Path("src/services/dialog/dialog_service.py").exists()
    assert not Path("src/services/dialog/dialog_pipeline_assembler.py").exists()
    assert not Path("src/services/inbound/inbound_gate_service.py").exists()
    assert not Path("src/services/context/core_context_builder.py").exists()


def test_removed_bridge_modules_do_not_return() -> None:
    assert not Path("src/services/hubspot_service.py").exists()
    assert not Path("src/services/crm/service.py").exists()
    assert not Path("src/services/crm/idempotency.py").exists()
    assert not Path("src/integrations/hubspot/hubspot_sync_canon.py").exists()


def test_ingestion_crm_split_is_preserved() -> None:
    ingest_uc = _read("src/use_cases/lead/ingest_lead_patch_use_case.py")
    workflow_uc = _read("src/use_cases/lead/process_lead_workflow_output_use_case.py")

    for forbidden in ("hubspot_service", "upsert_contact_properties", "ensure_contact_id"):
        assert forbidden not in ingest_uc

    assert "ingest_lead_patch_use_case.execute(" in workflow_uc
    assert "sync_lead_crm_use_case.execute(" not in workflow_uc


def test_transitional_scope_is_guarded() -> None:
    violations = [v for v in run_architecture_checks() if v.rule in {
        "legacy_resurrection",
        "transitional_scope_expansion",
        "transitional_scope_missing_vertex",
        "transitional_scope_missing_adapters",
        "orphan_legacy_wrapper",
        "backend_behavior_text_leakage",
        "scripts_legacy_smoke_resurrection",
    }]
    assert violations == []

    assert Path("src/llm/vertex/vertex_provider.py").exists()
    assert Path("src/adapters").exists()


def test_legacy_memory_runtime_layer_is_removed() -> None:
    assert not Path("src/memory_layer").exists()
    assert not Path("src/runtime_agents/memory_agent").exists()
    assert not Path("src/llm/tasks/memory").exists()
    assert not Path("src/domain/memory").exists()


def test_runtime_and_llm_paths_do_not_import_adk_agents() -> None:
    checked_files = [
        *[str(path.relative_to(REPO_ROOT)) for path in (REPO_ROOT / "src/runtime_agents").rglob("*.py")],
    ]

    for rel_path in checked_files:
        content = _read(rel_path)
        assert "src.adk_agents" not in content
        assert ".adk_agents." not in content


def test_llm_structured_routing_policy_matches_current_registry_tasks() -> None:
    routing = _read("src/llm/provider_routing.py")
    assert "REPLY_RUNTIME_TASKS" in routing
    assert '"profile_extract_task"' in routing
    assert '"legacy_memory_daily_summary_task"' not in routing
