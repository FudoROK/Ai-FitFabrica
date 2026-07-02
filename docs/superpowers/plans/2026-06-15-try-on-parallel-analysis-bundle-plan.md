# Try-On Parallel Analysis Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mandatory parallel Human Identity, Garment Identity, and Material / Texture analysis before Try-On generation.

**Architecture:** A focused analysis-bundle service invokes three provider-neutral ports concurrently. The Try-On workflow persists validated snapshots as child entities and fails closed before generation or billing when any required analysis fails.

**Tech Stack:** FastAPI, Pydantic, asyncio, SQLAlchemy, Alembic, PostgreSQL, canonical AgentInvocationService, pytest.

---

### Task 1: Domain And Analysis Bundle Contract

**Files:**
- Create: `src/domain/try_on_analysis.py`
- Modify: `src/domain/try_on.py`
- Modify: `src/use_cases/try_on/ports.py`
- Create: `src/use_cases/try_on/analysis_bundle_service.py`
- Test: `tests/test_try_on_analysis_bundle.py`

- [x] Add failing tests for strict snapshots, parallel execution, and fail-closed errors.
- [x] Implement provider-neutral analysis ports and bundle service.
- [x] Run analysis-bundle tests.

### Task 2: Garment And Material Adapters

**Files:**
- Create: `src/adapters/agents/try_on_garment_identity_analysis.py`
- Create: `src/adapters/agents/try_on_material_texture_analysis.py`
- Create: deterministic test adapters under `src/adapters/agents/`
- Create: `src/use_cases/try_on/analysis_errors.py`
- Test: `tests/test_try_on_garment_material_analysis_adapters.py`

- [x] Add failing mapping, artifact-reference, confidence, uncertainty, and failure tests.
- [x] Implement canonical invocation adapters and deterministic test adapters.
- [x] Run adapter tests.

### Task 3: Persistence

**Files:**
- Modify: `src/adapters/database/sql/try_on_models.py`
- Modify: `src/adapters/database/sql/try_on_serialization.py`
- Modify: `src/adapters/database/sql/try_on_repositories.py`
- Create: `alembic/versions/20260615_000015_try_on_analysis_bundle.py`
- Test: `tests/test_try_on_analysis_bundle_sql.py`
- Test: `tests/test_try_on_analysis_bundle_migration.py`

- [x] Add failing SQL round-trip and migration tests.
- [x] Implement one-to-one garment and material analysis child entities.
- [x] Run persistence tests.

### Task 4: Workflow And Runtime Wiring

**Files:**
- Modify: `src/use_cases/try_on/workflow_execution.py`
- Modify: `src/use_cases/try_on/workflow_service.py`
- Modify: `src/entrypoints/runtime_dependency_workflow_builders.py`
- Modify: `src/entrypoints/runtime_dependency_contracts.py`
- Modify: settings models
- Test: `tests/test_try_on_human_identity_workflow.py`
- Test: `tests/test_try_on_runtime_wiring.py`
- Test: architecture guardrails

- [x] Add failing workflow and wiring tests.
- [x] Persist all analyses before generation and fail closed with zero credits.
- [x] Run targeted workflow/runtime tests.

### Task 5: Verification And Staging

**Files:**
- Modify: active system documentation and backend catalog.

- [x] Run architecture, compile, targeted, full backend, and frontend gates.
- [x] Deploy migration and backend.
- [x] Run real staging analysis-bundle smoke and verify three invocation ledger rows.
