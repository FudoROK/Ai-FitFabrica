# Business Catalog Search Indexing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backend-owned pipeline that indexes approved B2B catalog products into the products vector namespace for Similar Search.

**Architecture:** Approved catalog records are projected into safe search records, converted into stable embedding text, embedded through the provider-neutral embedding port, and upserted through the vector index port. Runtime wiring keeps Qdrant/provider details in adapters, while business/use-case code stays portable. Manual reindex script is added for staging and tomorrow's catalog test.

**Tech Stack:** FastAPI backend use cases, Pydantic domain models, existing provider-neutral embedding port, Qdrant vector adapter, SQL/in-memory B2B catalog repositories, pytest.

---

### Task 1: Search Index Use Case

**Files:**
- Create: `src/use_cases/business_catalog/search_indexing.py`
- Modify: `src/use_cases/business_catalog/ports.py`
- Test: `tests/test_business_catalog_search_indexing.py`

- [x] Add a use-case service that accepts projected approved catalog records and writes `VectorPointRecord` items into `VectorNamespace.PRODUCTS`.
- [x] Build deterministic embedding text from title, category, description, location, delivery, price, and source metadata.
- [x] Use provider-neutral `EmbeddingRequest` and vector upsert port.

### Task 2: Repository Approved Search Records

**Files:**
- Modify: `src/adapters/business_catalog/in_memory_repository.py`
- Modify: `src/adapters/database/sql/business_catalog_repositories.py`
- Test: `tests/test_business_catalog_search_projection.py`

- [x] Add `list_approved_search_records(limit)` on B2B catalog repositories.
- [x] Return only active + approved records with sellable offers using the existing projector.

### Task 3: Runtime Wiring and Reindex Script

**Files:**
- Modify: `src/entrypoints/runtime_dependency_contracts.py`
- Modify: `src/entrypoints/runtime_dependency_workflow_builders.py`
- Create: `scripts/reindex_business_catalog_search.py`
- Test: `tests/test_business_catalog_search_indexing_script.py`

- [x] Wire `BusinessCatalogSearchIndexingService` into runtime dependencies.
- [x] Add a script that loads runtime dependencies and reindexes approved catalog records.
- [x] Print indexed/skipped counts for staging smoke.

### Task 4: Verification and Docs

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Modify: `docs/04_OWNER_REMAINING_WORK.md`

- [x] Run targeted backend tests.
- [x] Run architecture guardrail.
- [x] Run `compileall`.
- [x] Note that manual website test is moved to tomorrow.

### Completion Notes

- Added provider-neutral indexing service for approved B2B catalog products.
- Added repository projection listing for in-memory and SQL catalog repositories.
- Added runtime bundle and `scripts/reindex_business_catalog_search.py`.
- Added Qdrant products collection bootstrap before vector upsert.
- Manual website catalog population/search test is intentionally moved to the next working session.
