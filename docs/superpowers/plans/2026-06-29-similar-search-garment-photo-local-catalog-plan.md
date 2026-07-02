# Similar Search Garment Photo Local Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect `/workspace/similar-search` to a backend-owned flow where a user uploads a garment photo, backend analyzes the garment, and returns similar approved products from the local B2B catalog first.

**Architecture:** Frontend remains a thin client and sends a multipart request to FastAPI. Backend stores/validates the uploaded image, invokes Garment Identity through an adapter boundary, builds a typed search profile, runs existing vector search when available, and falls back to approved local B2B catalog records when the vector index is empty. No external marketplace scraping is introduced.

**Tech Stack:** FastAPI, Pydantic, existing AgentInvocationService/Garment Identity adapter contour, PostgreSQL/B2B catalog repository, Next.js/React/TypeScript.

---

### Task 1: Extend Similar Search Domain for Garment Photo Input

**Files:**
- Modify: `src/domain/similar_search.py`
- Modify: `src/use_cases/similar_search/query_preparation.py`
- Test: `tests/test_similar_search_domain_models.py`
- Test: `tests/test_similar_search_query_preparation.py`

- [ ] Add `source_type="garment_photo"` support and a structured `garment_profile` field.
- [ ] Add tests proving `garment_photo` requests require backend-populated garment profile, not browser-side AI fields.
- [ ] Add query preparation tests proving garment type, color, silhouette, and preserved details become the embedding/search input.

### Task 2: Add Local Catalog Fallback Port

**Files:**
- Modify: `src/use_cases/similar_search/ports.py`
- Modify: `src/use_cases/similar_search/workflow_service.py`
- Modify: `src/adapters/database/sql/business_catalog_repositories.py`
- Modify: `src/adapters/business_catalog/in_memory_repository.py`
- Test: `tests/test_similar_search_workflow_service.py`
- Test: `tests/test_business_catalog_search_projection.py`

- [ ] Add a repository method for approved searchable B2B catalog records by category/color text.
- [ ] Use vector retrieval first; if it returns no hydrated matches, use local approved B2B catalog fallback.
- [ ] Preserve location-first ranking and source trust fields.

### Task 3: Add Multipart Garment Photo Route

**Files:**
- Modify: `src/entrypoints/similar_search_routes.py`
- Modify: `src/entrypoints/runtime_dependency_contracts.py`
- Modify: `src/entrypoints/runtime_dependency_workflow_builders.py`
- Test: `tests/test_similar_search_routes.py`
- Test: `tests/test_similar_search_runtime_wiring.py`

- [ ] Add `POST /api/similar-search/garment-photo` accepting `garment_photo`, optional budget, country, city, and limit.
- [ ] Validate content type and size on backend.
- [ ] Store image through object storage and invoke Garment Identity through runtime dependencies.
- [ ] Return the same typed `SimilarSearchResponse` as the existing route.

### Task 4: Connect Frontend Page

**Files:**
- Modify: `apps/web/src/lib/api/contracts.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Replace/modify: `apps/web/src/app/(workspace)/workspace/similar-search/page.tsx`
- Test: `tests/test_workspace_similar_search_page.py` or existing workspace page guardrails

- [ ] Add typed frontend contracts and API client method.
- [ ] Replace placeholder text with a real form: garment photo, budget, country, city.
- [ ] Add validation, preview, loading, error, empty, and success states.
- [ ] Show location explanation and cheaper alternative flags from backend results.

### Task 5: Verification and Documentation

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Modify: `docs/04_OWNER_REMAINING_WORK.md`

- [ ] Run targeted backend tests for Similar Search, Garment Identity route integration, and B2B catalog projection.
- [ ] Run architecture guardrail and `compileall`.
- [ ] Run frontend lint, typecheck, and build.
- [ ] Update docs/action log with implemented scope and remaining limitations.
