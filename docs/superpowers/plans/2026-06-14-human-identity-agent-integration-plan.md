# Human Identity Agent Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Human Identity Agent a mandatory, audited, fail-closed backend gate before Try-On generation.

**Architecture:** A dedicated `HumanIdentityAnalysisService` invokes the canonical `AgentInvocationService`, validates the versioned agent output, and applies backend continuation policy. The typed result is stored inside the Try-On aggregate and persisted through a focused SQL child table. Try-On execution only sees the dedicated analysis port and never imports an ADK agent root.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, PostgreSQL, Google ADK provider runtime, pytest.

---

### Task 1: Domain Analysis Snapshot And Backend Policy

**Files:**
- Modify: `src/domain/try_on.py`
- Create: `src/use_cases/try_on/human_identity_policy.py`
- Test: `tests/test_try_on_human_identity_policy.py`

- [ ] Write failing tests proving that a valid analysis may continue and that missing face visibility, empty body regions, low confidence, high uncertainty, or absent preservation targets are rejected.
- [ ] Run `.venv\Scripts\python.exe -m pytest tests/test_try_on_human_identity_policy.py -q` and confirm failure because the policy and snapshot do not exist.
- [ ] Add typed `TryOnHumanIdentityAnalysis`, `TryOnHumanIdentityVerdict`, and rejection-reason models to the Try-On domain.
- [ ] Implement a fail-closed `HumanIdentityContinuationPolicy` with backend-owned minimum confidence configuration.
- [ ] Add `ANALYZING_HUMAN` status and typed error codes `HUMAN_IDENTITY_ANALYSIS_FAILED` and `HUMAN_IDENTITY_INPUT_NOT_SUITABLE`.
- [ ] Run the policy tests and confirm they pass.

### Task 2: Canonical Human Identity Analysis Adapter

**Files:**
- Create: `src/adapters/agents/human_identity_analysis.py`
- Modify: `src/use_cases/try_on/ports.py`
- Test: `tests/test_try_on_human_identity_analysis_service.py`

- [ ] Write failing tests proving the service builds a versioned `AgentInvocationRequest`, passes only the approved human object key, maps valid output into the Try-On snapshot, and maps invocation/validation failure into typed safe failure.
- [ ] Run the targeted tests and confirm failure because the service does not exist.
- [ ] Define `HumanIdentityAnalysisPort` and typed safe analysis exceptions/results.
- [ ] Implement `HumanIdentityAnalysisAdapter` using `AgentInvocationService`, `HumanIdentityRequest`, `HumanIdentityContract`, the versioned prompt/config, and backend continuation policy. Keep all `src.adk_agents` imports outside use cases.
- [ ] Ensure the service never stores raw prompt/provider payload or image bytes in the Try-On snapshot.
- [ ] Run the targeted tests and confirm they pass.

### Task 3: Mandatory Try-On Execution Gate

**Files:**
- Modify: `src/domain/try_on.py`
- Modify: `src/use_cases/try_on/workflow_execution.py`
- Modify: `src/use_cases/try_on/workflow_service.py`
- Test: `tests/test_try_on_human_identity_workflow.py`
- Modify: existing Try-On workflow tests as required for the new mandatory dependency.

- [ ] Write failing tests proving successful analysis is persisted before generation and that failed/rejected analysis prevents generation and billing.
- [ ] Run the targeted tests and confirm the expected failures.
- [ ] Add nullable `human_identity_analysis` to `TryOnJob` for backward-compatible reads.
- [ ] Inject `HumanIdentityAnalysisPort` into `TryOnWorkflowService`.
- [ ] Execute and persist Human Identity analysis before calling `TryOnGenerationPort`.
- [ ] On analysis failure, persist a typed failed job with zero charged credits and no generation call.
- [ ] Run all Try-On workflow tests and confirm they pass.

### Task 4: Durable SQL Persistence And Migration

**Files:**
- Modify: `src/adapters/database/sql/try_on_models.py`
- Modify: `src/adapters/database/sql/try_on_serialization.py`
- Modify: `src/adapters/database/sql/try_on_repositories.py`
- Create: `alembic/versions/20260614_000012_try_on_human_identity_analysis.py`
- Modify: `tests/test_try_on_sql_repository.py`
- Create: `tests/test_try_on_human_identity_sql_migration.py`

- [ ] Write failing repository and migration tests proving analysis round-trip and compatibility with jobs without analysis.
- [ ] Run the targeted tests and confirm failure because the SQL child table does not exist.
- [ ] Add `TryOnHumanIdentityAnalysisRow` with one-to-one `job_id`, typed metadata columns, and JSON payload only for the validated analysis contract.
- [ ] Update serialization/repository save/get/list paths.
- [ ] Add an Alembic migration with downgrade support.
- [ ] Run repository and migration tests and confirm they pass.

### Task 5: Runtime Wiring And Architecture Guardrails

**Files:**
- Modify: `src/entrypoints/runtime_dependency_contracts.py`
- Modify: `src/entrypoints/runtime_dependency_workflow_builders.py`
- Modify: `src/settings_model_try_on.py`
- Modify: `src/settings_contracts.py` if required by the existing settings facade.
- Test: `tests/test_try_on_human_identity_runtime_wiring.py`
- Modify: `tests/architecture/test_agent_runtime_guardrails.py`

- [ ] Write failing tests proving Try-On runtime receives the canonical invocation service and builds Human Identity analysis with configured timeout/model/confidence threshold.
- [ ] Add settings for Human Identity timeout, preferred model, and minimum confidence with safe defaults.
- [ ] Wire `HumanIdentityAnalysisAdapter` into `TryOnWorkflowService`.
- [ ] Add architecture guardrails forbidding Try-On routes/workflows from importing Human Identity ADK roots or direct provider clients.
- [ ] Run runtime and architecture tests and confirm they pass.

### Task 6: Verification, Documentation, And Staging

**Files:**
- Modify: `docs/current_system_full_documentation.md`
- Modify: `docs/backend_file_catalog.md`
- Modify: `docs/tests_description.md`
- Modify: `docs/superpowers/plans/2026-06-13-fitfabrica-agent-production-runtime-plan.md`

- [ ] Document the mandatory Human Identity gate, persisted analysis, failure policy, and remaining Wave 3 agents.
- [ ] Run `.venv\Scripts\python.exe scripts\check_architecture.py`.
- [ ] Run `.venv\Scripts\python.exe -m compileall -q src`.
- [ ] Run `.venv\Scripts\python.exe -m pytest -q -x --maxfail=1`.
- [ ] Run frontend lint, typecheck, and production build.
- [ ] Deploy the backend slice and migration to staging.
- [ ] Verify migration head, API/worker health, public endpoints, safe logs, valid analysis audit persistence, and failure behavior without generation or billing.
