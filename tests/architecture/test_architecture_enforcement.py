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


def test_dialog_service_stays_thin_facade() -> None:
    text = _read("src/services/dialog/dialog_service.py")
    forbidden_tokens = (
        "extract_patch(",
        "non_empty_patch(",
        "derive_lead_state_flags(",
        "build_hubspot_profile_from_lead(",
        "map_domain_profile_to_hubspot_properties(",
        "normalize_lead_patch(",
        "build_extraction_prompt(",
        "generate_reply_use_case.llm_service =",
        "handle_inbound_message_use_case.llm_service =",
    )
    for token in forbidden_tokens:
        assert token not in text

    required_tokens = (
        "self.inbound_gate_service.prepare(",
        "self.dialog_orchestrator.execute(",
        "DialogPipelineAssembler(",
    )
    for token in required_tokens:
        assert token in text


def test_legacy_bridges_are_removed() -> None:
    assert not Path("src/services/hubspot_service.py").exists()
    assert not Path("src/services/crm/service.py").exists()
    assert not Path("src/services/crm/idempotency.py").exists()
    assert not Path("src/integrations/hubspot/hubspot_sync_canon.py").exists()


def test_ingestion_crm_split_is_preserved() -> None:
    ingest_uc = _read("src/use_cases/lead/ingest_lead_patch_use_case.py")
    workflow_uc = _read("src/use_cases/lead/process_lead_workflow_output_use_case.py")
    inbound_uc = _read("src/use_cases/dialog/handle_inbound_message_use_case.py")

    for forbidden in ("hubspot_service", "upsert_contact_properties", "ensure_contact_id"):
        assert forbidden not in ingest_uc

    assert "ingest_lead_patch_use_case.execute(" in workflow_uc
    assert "sync_lead_crm_use_case.execute(" not in workflow_uc
    assert "process_lead_workflow_output_use_case.execute(" in inbound_uc
    assert "def _ingest_workflow_output(" not in inbound_uc


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


def test_memory_runtime_uses_task_registry_path() -> None:
    memory_runtime = _read("src/memory_layer/services/memory_sync_llm_service.py")
    memory_orchestrator = _read("src/memory_layer/services/memory_sync_port.py")
    assert "self.llm_service.run(" in memory_runtime
    assert 'task="memory_daily_sync_task"' in memory_runtime
    assert "VertexProvider" not in memory_runtime
    assert "_run_memory_agent(" not in memory_runtime
    assert "atomic_save_memory_artifacts(" not in memory_orchestrator


def test_runtime_and_llm_paths_do_not_import_adk_agents() -> None:
    checked_files = [
        "src/memory_layer/services/memory_sync_llm_service.py",
        "src/memory_layer/services/memory_sync_port.py",
        "src/memory_layer/use_cases/process_daily_agent_output_use_case.py",
        "src/memory_layer/use_cases/process_rolling_memory_agent_output_use_case.py",
        "src/memory_layer/use_cases/apply_daily_agent_output_use_case.py",
        "src/memory_layer/use_cases/apply_rolling_memory_agent_output_use_case.py",
        "src/llm/tasks/helpers/memory_output_parser.py",
        "src/llm/tasks/primary_agent/primary_agent_reply_task.py",
        "src/llm/tasks/memory/memory_daily_sync_task.py",
        "src/llm/tasks/memory/memory_rolling_sync_task.py",
        *[str(path.relative_to(REPO_ROOT)) for path in (REPO_ROOT / "src/runtime_agents").rglob("*.py")],
    ]

    for rel_path in checked_files:
        content = _read(rel_path)
        assert "src.adk_agents" not in content
        assert ".adk_agents." not in content


def test_llm_structured_routing_policy_matches_current_registry_tasks() -> None:
    routing = _read("src/llm/provider_routing.py")
    assert '"primary_agent_reply_task"' in routing
    assert '"profile_extract_task"' in routing
    assert '"memory_daily_sync_task"' in routing
    assert '"memory_rolling_sync_task"' in routing
    assert '"legacy_memory_daily_summary_task"' not in routing
