# Product Card Garment Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mandatory persisted Garment Identity stage before real Product Card generation.

**Architecture:** Product Card orchestration invokes a provider-neutral garment-analysis port, persists its validated output, then passes the persisted structured analysis to the provider-neutral Product Card generation port. Both production adapters use the canonical `AgentInvocationService`.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, portable object storage, canonical agent runtime, Gemini staging provider.

---

### Task 1: Domain And Contracts

**Files:**
- Modify: `src/domain/product_card.py`
- Modify: `src/use_cases/product_card/ports.py`
- Test: `tests/test_product_card_domain_models.py`

- [x] Add failing tests for strict persisted garment analysis and generation receiving structured analysis.
- [x] Add `ProductCardGarmentAnalysis` and the required port signatures.
- [x] Run domain tests.

### Task 2: Garment Identity Adapter

**Files:**
- Create: `src/adapters/agents/garment_identity_analysis.py`
- Create: `src/adapters/agents/deterministic_garment_identity_analysis.py`
- Create: `src/use_cases/product_card/garment_identity_errors.py`
- Test: `tests/test_product_card_garment_identity_adapter.py`

- [x] Add failing adapter tests for artifact integrity, output mapping, confidence policy, and safe failure.
- [x] Implement canonical invocation adapter and deterministic test adapter.
- [x] Run adapter tests.

### Task 3: Persistence And Migration

**Files:**
- Modify: `src/adapters/database/sql/product_card_models.py`
- Modify: `src/adapters/database/sql/product_card_repositories.py`
- Modify: `src/adapters/product_card/in_memory_repository.py`
- Create: `alembic/versions/20260615_000014_product_card_garment_analysis.py`
- Test: `tests/test_product_card_sql_models.py`
- Test: `tests/test_product_card_sql_repositories.py`
- Test: `tests/test_product_card_garment_analysis_migration.py`

- [x] Add failing persistence and migration tests.
- [x] Implement one-to-one garment-analysis persistence.
- [x] Run persistence tests.

### Task 4: Product Card Orchestration

**Files:**
- Modify: `src/use_cases/product_card/workflow_service.py`
- Modify: `src/adapters/agents/product_card_generation.py`
- Modify: `src/adapters/product_card/fake_generation.py`
- Test: `tests/test_product_card_workflow_service.py`
- Test: `tests/test_product_card_agent_generation_adapter.py`

- [x] Add failing tests proving analysis runs and persists before generation.
- [x] Pass saved structured analysis to Product Card Agent without image artifacts.
- [x] Prove analysis failure marks the job failed and blocks generation/charging.
- [x] Run workflow tests.

### Task 5: Runtime And API

**Files:**
- Modify: `src/entrypoints/runtime_dependency_product_card_builder.py`
- Modify: `src/entrypoints/product_card_routes.py`
- Modify: `src/settings_model_providers.py`
- Test: `tests/test_product_card_runtime_wiring.py`
- Test: `tests/test_product_card_routes.py`
- Test: `tests/architecture/test_product_card_guardrails.py`

- [x] Add failing runtime, route, and provider-isolation tests.
- [x] Wire test-only deterministic adapter and production canonical adapter.
- [x] Expose the saved garment-analysis endpoint.
- [x] Run targeted tests.

### Task 6: Documentation, Deployment, And Real Smoke

**Files:**
- Modify: `docs/current_system_full_documentation.md`
- Modify: `docs/backend_file_catalog.md`

- [x] Update active system documentation.
- [x] Run full backend/frontend verification.
- [x] Deploy backend and migration to staging.
- [x] Run real Product Card smoke and verify both agent invocation ledger rows.
- [x] Verify public endpoints and logs.
