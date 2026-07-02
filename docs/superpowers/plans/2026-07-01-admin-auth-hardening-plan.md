# Admin Auth Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop public admin routes from trusting browser-supplied admin identity headers by default.

**Architecture:** Add a backend-owned admin auth helper that accepts `Authorization: Bearer <token>` matched against an environment secret. Keep legacy `x-fitfabrica-admin-*` headers only behind an explicit unsafe staging flag. Update admin API clients and admin UI so tokens are entered as an access token, not as an admin id/role pair.

**Tech Stack:** FastAPI, Pydantic settings, Next.js, TypeScript.

---

### Task 1: Settings And Backend Auth Helper

**Files:**
- Modify: `src/settings_model_app.py`
- Create: `src/entrypoints/admin_auth.py`

- [ ] Add `ADMIN_API_TOKEN` and `ALLOW_UNSAFE_ADMIN_HEADER_AUTH` settings.
- [ ] Create `resolve_admin_actor` helper.
- [ ] Require bearer token when unsafe header auth is disabled.

### Task 2: Admin Routes

**Files:**
- Modify: `src/entrypoints/admin_business_catalog_routes.py`
- Modify: `src/entrypoints/admin_taxonomy_routes.py`

- [ ] Replace direct role/id header trust with `resolve_admin_actor`.
- [ ] Keep existing feature flags.
- [ ] Return structured 403 on missing or invalid admin token.

### Task 3: Frontend Admin Client

**Files:**
- Modify: `apps/web/src/lib/api/admin-contracts.ts`
- Modify: `apps/web/src/lib/api/business-catalog-contracts.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Modify: `apps/web/src/features/admin/business-catalog-review.tsx`
- Modify: `apps/web/src/features/admin/business-accounts.tsx`
- Modify: `apps/web/src/features/admin/taxonomy-review.tsx`

- [ ] Change admin credentials to `adminToken`.
- [ ] Send `Authorization: Bearer <adminToken>`.
- [ ] Remove role/id headers from frontend API client.
- [ ] Rename UI input from admin actor id to admin access token.

### Task 4: Tests

**Files:**
- Modify: admin route tests and admin page guardrails.

- [ ] Add tests for bearer token success.
- [ ] Add tests for missing/invalid token failures.
- [ ] Add tests showing unsafe header auth requires explicit setting.
- [ ] Run backend and frontend verification.
