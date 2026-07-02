# Similar Search Analytics v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show admins a first read-only analytics view for free Similar Search clicks.

**Architecture:** Reuse the existing backend-owned `similar_search_click_events` table. Add typed aggregate DTOs, repository methods for summary/top-products/top-marketplaces/top-cities, an admin API endpoint under `/api/admin/business-catalog/analytics/similar-search`, and a small panel on `/admin/business-catalog`.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Next.js, TypeScript.

---

### Task 1: Backend Analytics Contracts

**Files:**
- Modify: `src/domain/similar_search.py`
- Modify: `src/use_cases/similar_search/ports.py`
- Modify: `src/use_cases/similar_search/events.py`

- [ ] Add `SimilarSearchClickAnalyticsItem`, `SimilarSearchClickAnalyticsSummary`, and `SimilarSearchClickAnalyticsResponse`.
- [ ] Add repository port method `get_click_analytics(limit: int)`.
- [ ] Add service method `get_analytics(limit: int)`.

### Task 2: Repository Aggregation

**Files:**
- Modify: `src/adapters/similar_search/in_memory_event_repository.py`
- Modify: `src/adapters/database/sql/similar_search_repositories.py`

- [ ] Implement in-memory grouping for tests/local fallback.
- [ ] Implement SQL grouping from `similar_search_click_events`.
- [ ] Keep analytics read-only and avoid exposing user-level data.

### Task 3: Admin API

**Files:**
- Modify: `src/entrypoints/admin_business_catalog_routes.py`

- [ ] Add `GET /api/admin/business-catalog/analytics/similar-search`.
- [ ] Reuse existing admin role headers and feature flag.
- [ ] Return typed analytics response.

### Task 4: Frontend Admin Panel

**Files:**
- Modify: `apps/web/src/lib/api/business-catalog-contracts.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Modify: `apps/web/src/features/admin/business-catalog-review.tsx`

- [ ] Add TypeScript analytics contracts.
- [ ] Add API client method.
- [ ] Add a “Similar Search Analytics” panel with total clicks, redirect clicks, local-only clicks, top products, marketplaces, and cities.

### Task 5: Verification

**Files:**
- Modify: `tests/test_similar_search_click_events.py`
- Modify: `tests/test_similar_search_routes.py`
- Modify: `tests/test_admin_business_catalog_page.py`

- [ ] Add backend service/repository tests.
- [ ] Add admin route test.
- [ ] Add frontend guardrail test.
- [ ] Run targeted backend tests, frontend lint/typecheck/build, architecture guardrail, and compileall.
