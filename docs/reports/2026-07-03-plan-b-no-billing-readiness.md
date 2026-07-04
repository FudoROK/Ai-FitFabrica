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
- Added protected `GET /ready` no-billing readiness diagnostics. The endpoint reports SQL, Redis, object storage, Qdrant, auth, billing, AI provider, image editing, search discovery, and admin-surface configuration without calling paid providers.
- Extended status endpoint security guardrails so `/ready` follows the same token/loopback/public-opt-in policy as `/health` and `/time`.
- Added internal frontend route `/admin/readiness` behind `NEXT_PUBLIC_ENABLE_ADMIN_READINESS_UI=true`. The page uses the typed API client, requires `STATUS_ENDPOINT_TOKEN`, reads backend `/ready`, and renders blockers, safe no-billing flows, service statuses, and post-billing checks.
- Added frontend acceptance guardrails that keep README route documentation aligned with the Next app tree, prevent `href="#"` placeholder links, and require active frontend forms to use real submit handlers.
- Added `scripts/post_billing_acceptance_gate.py` and `docs/runbooks/post_billing_acceptance_gate.md` so the operator can run a local artifact gate and optional deployed `/ready` gate before paid acceptance.
- Added `scripts/no_billing_acceptance_gate.py` and `docs/runbooks/no_billing_acceptance_gate.md` so pre-billing backend/frontend readiness can be checked with one local command.
- Added `scripts/staging_no_billing_smoke.py` and deploy runbook instructions for safe deployed checks that avoid paid AI/provider calls.

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
- `GET /ready`: returns a backend-owned no-billing readiness map, expected blockers, flows safe to test before billing, and post-billing checks.
- `/admin/readiness`: internal admin diagnostics UI for the same readiness contract; not linked from workspace navigation.

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
- `pytest tests/test_status_routes_health_runtime.py tests/test_runtime_security.py -q` -> passed after adding `/ready`
- `pytest tests/test_admin_readiness_page.py -q` -> passed after adding `/admin/readiness`
- `npm run typecheck` -> passed after adding typed frontend readiness contracts
- `pytest tests/test_no_billing_frontend_guardrails.py tests/test_frontend_route_documentation.py tests/test_public_frontend_routes.py tests/test_admin_readiness_page.py tests/test_admin_business_catalog_page.py tests/test_admin_business_accounts_page.py tests/test_admin_taxonomy_page.py -q` -> `15 passed`
- `npm run lint`, `npm run typecheck`, and `npm run build` -> passed after frontend acceptance sweep; build rendered 38 active routes.
- `pytest tests/test_post_billing_acceptance_gate.py -q` -> passed after adding the executable post-billing gate.
- `python scripts/post_billing_acceptance_gate.py` -> returned `readiness_status=ready` for local artifact checks and skipped deployed `/ready` when no API URL was provided.
- `pytest tests/test_no_billing_acceptance_gate.py -q` -> passed after adding the executable no-billing local gate.
- `python scripts/no_billing_acceptance_gate.py` -> returned `readiness_status=ready`; it ran 49 targeted backend/frontend guardrail tests, post-billing artifact gate, architecture guardrail, `compileall`, web `typecheck`, web `lint`, and web `build`.
- `pytest tests/test_staging_no_billing_smoke_script.py tests/test_deploy_runbook_no_billing_smoke.py -q` -> passed after adding the staging no-billing smoke script and deploy runbook coverage.

## Remaining Work After Billing/Auth Restoration

- Connect production authentication provider and replace the fail-closed `/auth/sign-in` behavior with real session creation.
- Restore backend billing core/provider access and clear `/ready` blockers for `billing`, `auth`, `ai_provider`, and approved discovery sources.
- Run paid provider smokes for Gemini/Vertex-backed flows.
- Run browser-level acceptance for Try-On, B2B category validation, Product Card, Similar Search garment-photo, and billing guardrails.
- Keep admin UI and candidate review behind bearer-token protected admin routes.
