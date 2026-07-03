# Plan B No-Billing Readiness Report - 2026-07-03

## Scope

Plan B focused on work that can be completed before Google/Gemini billing is restored:

- keep backend-first behavior;
- remove fake public auth/contact actions;
- make public website form submissions durable;
- keep paid AI/provider workflows disabled or fail-closed until billing is restored;
- verify backend and frontend locally.

## Changes Completed

- Added `public_demo_requests` PostgreSQL table through Alembic migration `20260703_000026_public_demo_requests`.
- Added backend domain/use-case/repository layers for public demo/contact requests.
- Added SQL repository with in-memory fallback for local/test runtime only.
- Added `POST /demo-request` to persist public contact/demo requests.
- Added `POST /auth/sign-in` as a fail-closed endpoint returning structured `503 auth_not_configured` until production auth is connected.
- Registered public request routes in the main HTTP router.
- Added required public route aliases `/login` and `/contact`.
- Updated public sign-in UI to remove decorative Google OAuth and password-recovery buttons until real auth contracts exist.
- Updated public navigation/footer to prefer `/login` and `/contact`.
- Canonicalized remaining public CTAs from legacy `/contacts` to `/contact`, while keeping `/contacts` as a compatibility alias.
- Added frontend no-billing guardrails so active workspace pages use loading/error/empty shell states instead of silently rendering blank content when workspace bootstrap is unavailable.

## SQL Tables Added

### `public_demo_requests`

Stores public website demo/contact requests:

- `request_id`
- `name`
- `email`
- `company`
- `message`
- `status`
- `created_at`

## Endpoints/Flows Using SQL Persistence

- `POST /demo-request`: persists public contact/demo requests in PostgreSQL when SQL is configured.
- `POST /auth/sign-in`: intentionally does not authenticate yet; it fails closed until the production auth contour is connected.

## Verification

Fresh local verification passed:

- `pytest tests/test_public_request_routes.py tests/test_public_frontend_routes.py tests/test_public_request_sql_migration.py tests/test_workspace_text_encoding.py -q` -> `7 passed`
- `python scripts/check_architecture.py` -> passed
- `python -m compileall -q src tests` -> passed
- `npm run typecheck` -> passed
- `npm run lint` -> passed
- `npm run build` -> passed
- targeted backend/frontend adjacent suite -> `32 passed`
- full backend pytest -> `1141 passed`, with one existing Authlib deprecation warning
- no-billing frontend guardrails -> `2 passed`
- workspace/public adjacent frontend guardrails -> `8 passed`
- refreshed web `typecheck`, `lint`, and `build` after route/state hardening -> passed

## Remaining Work After Billing/Auth Restoration

- Connect production authentication provider and replace the fail-closed `/auth/sign-in` behavior with real session creation.
- Run paid provider smokes for Gemini/Vertex-backed flows.
- Run browser-level acceptance for Try-On, B2B category validation, Product Card, Similar Search garment-photo, and billing guardrails.
- Keep admin UI and candidate review behind bearer-token protected admin routes.
