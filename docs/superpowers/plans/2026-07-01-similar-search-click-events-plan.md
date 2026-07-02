# Similar Search Click Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make free Similar Search measurable by recording when a user opens a found product.

**Architecture:** Backend remains the single owner of analytics. Search results expose a safe `offer_url`, while the frontend opens a backend redirect endpoint that records a click event before sending the user to the product URL. Events are persisted in PostgreSQL when SQL is configured and use an in-memory repository in tests/local fallback.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, PostgreSQL, Next.js, TypeScript.

---

### Task 1: Result Contract And Event Domain

**Files:**
- Modify: `src/domain/similar_search.py`
- Modify: `src/use_cases/similar_search/ranking.py`
- Modify: `apps/web/src/lib/api/contracts.ts`

- [ ] Add `offer_url` to `SimilarSearchResult` so the backend can return the approved destination URL already stored in the catalog offer.
- [ ] Add typed event request/response models: `SimilarSearchClickEventRequest`, `SimilarSearchClickEvent`, `SimilarSearchClickEventResponse`.
- [ ] Add frontend contract fields for `offer_url` and click event response.

### Task 2: Event Persistence

**Files:**
- Create: `src/use_cases/similar_search/events.py`
- Modify: `src/use_cases/similar_search/ports.py`
- Create: `src/adapters/similar_search/in_memory_event_repository.py`
- Create: `src/adapters/database/sql/similar_search_models.py`
- Create: `src/adapters/database/sql/similar_search_repositories.py`
- Create: `alembic/versions/20260701_000023_similar_search_click_events.py`

- [ ] Add a service that validates product URL safety, creates a click event, saves it, and returns the redirect URL.
- [ ] Persist product id, title, marketplace, offer URL, image URL, user city/country, event source, and timestamps.
- [ ] Block unsafe internal schemes except `local://business-catalog/...`, which should be recorded but not redirected externally.

### Task 3: API Route And Runtime Wiring

**Files:**
- Modify: `src/entrypoints/runtime_dependency_contracts.py`
- Modify: `src/entrypoints/runtime_dependency_workflow_builders.py`
- Modify: `src/entrypoints/similar_search_routes.py`

- [ ] Add the event service to `SimilarSearchRuntimeDependencies`.
- [ ] Build SQL or in-memory event repository depending on infrastructure availability.
- [ ] Add `POST /api/similar-search/events/click` that records and returns event metadata.
- [ ] Add `GET /api/similar-search/redirect` that records and redirects to the offer URL, or returns a safe 409 for local-only offers.

### Task 4: Frontend CTA

**Files:**
- Modify: `apps/web/src/lib/api/client.ts`
- Modify: `apps/web/src/features/workspace/similar-search-workflow.tsx`

- [ ] Add a typed client helper for click event recording.
- [ ] Render “Посмотреть товар” on each result.
- [ ] Open the backend redirect URL instead of opening marketplace URLs directly.
- [ ] Keep disabled state for local-only offers where there is no external destination.

### Task 5: Verification And Docs

**Files:**
- Modify: `tests/test_similar_search_routes.py`
- Create: `tests/test_similar_search_click_events.py`
- Modify: `tests/test_workspace_similar_search_page.py`
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`

- [ ] Add tests for result `offer_url`, click event persistence, redirect behavior, local-only blocking, and frontend CTA wiring.
- [ ] Run targeted backend tests, frontend lint/typecheck, architecture guardrail, and compileall.
- [ ] Record the completed step in the project action log.
