# Full Project Monitoring Report - 2026-07-05

Цель: повторно проверить AI FitFabrica перед включением billing/provider access: ошибки, legacy, неработающие контуры, frontend/backend readiness, production blockers и то, что еще можно довести до enterprise-ready состояния без платного биллинга.

## Executive Status

Локальная pre-billing готовность подтверждена.

- `client_readiness_gate.py`: `readiness_status=ready`.
- `auth_readiness_gate.py`: `readiness_status=ready`.
- `billing_readiness_gate.py`: `readiness_status=ready`.
- `post_billing_acceptance_gate.py`: `readiness_status=ready` для local artifacts, deployed `/ready` skipped без URL.
- `check_architecture.py`: `ARCHITECTURE CHECK PASSED`.
- `no_billing_acceptance_gate.py`: `readiness_status=ready`, `failed_checks=0`.
- `no_billing_acceptance_gate.py --full-backend --skip-frontend-build`: `readiness_status=ready`, `1186 passed, 2 warnings`.

Известная residual test noise: после полного pytest в output остается служебная строка `RuntimeError: Event loop is closed`, но процесс завершается успешно и suite проходит. Это стоит отдельно зачистить как polish, но сейчас это не blocking failure.

## Customer Flow Readiness

Все customer-facing contours из `client_readiness_gate` проходят локальную pre-billing проверку:

- B2C public entry: routes, contact/demo request, fail-closed auth.
- B2C Try-On: upload UI, SQL job persistence, sandbox/no-paid generation contour, result shell, quality/repair contracts.
- B2C Similar Search: request/photo contract, local approved catalog search, click event persistence.
- B2C Outfit Builder: request/status contract and frontend states.
- B2B Business Catalog: merchant/product create/list, image metadata, CSV import, submit-to-review, SQL persistence.
- B2B Product Card: job creation, SQL persistence, garment analysis contract, safe non-paid generation adapter.
- B2B Content Package: job contract, SQL persistence, artifact metadata, frontend action wiring.
- B2B Pricing: pricing query preparation, ranking, SQL job persistence, provider-neutral workflow contract.
- B2B Admin Review: admin readiness, business catalog, taxonomy, business accounts, SQL-backed review actions.

## Billing/Auth/Provider Status

Prepared but intentionally disabled before external activation:

- Auth is fail-closed: no fake OAuth/session success.
- Billing core is disabled in env examples, but backend-owned ledger/service/repository contracts are present.
- Frontend credits page displays backend DTOs and does not calculate balances.
- Post-billing gate has required local artifacts for live acceptance.

External blockers remain:

- production auth provider activation;
- billing core activation;
- payment provider activation;
- live AI/provider access;
- approved marketplace/search source activation;
- deployed staging browser acceptance.

## Legacy And Fallback Findings

### Acceptable pre-billing/test-only items

- `sandbox_fake`, deterministic adapters, `FakeProvider`, and in-memory repositories are still present in tests and safe local/sandbox contours.
- Try-On real activation has fail-closed validation: real Vertex generation requires S3 object storage, PostgreSQL DSN, Redis queue, Redis URL, and Vertex project.
- Admin and readiness routes are protected by existing guardrails and fail-closed checks.

### Enterprise risks to keep visible

1. Runtime builders still contain several in-memory fallback paths when infrastructure is missing. This is acceptable for local tests, but production/staging readiness must keep verifying SQL/Redis/S3 are actually configured before any live customer flow.
2. There are large active files over 300 lines, including runtime builders, route modules, business catalog service/repositories, API client/contracts, Try-On workflow UI, and admin business catalog UI. They are working, but they are long-term maintenance risk.
3. Python quality configuration is not centralized in `pyproject.toml`; current quality relies on pytest, compileall, custom architecture checks, and frontend lint/typecheck.
4. Existing docs contain older status snapshots with mojibake display in PowerShell and outdated counts, for example older owner docs still mention previous test totals. Current source files read correctly as UTF-8 through Python, but old docs should be refreshed or archived for operator clarity.
5. Some public/workspace content still uses product placeholder structures by design. Existing guardrails prevent decorative broken links/forms, but future work should keep replacing placeholder presentation with backend-driven live data where the workflow is already implemented.

## Large Active Files

Files currently above the 300-line decomposition threshold:

- `src/use_cases/business_catalog/service.py`
- `src/entrypoints/admin_business_catalog_routes.py`
- `src/entrypoints/runtime_dependency_workflow_builders.py`
- `src/entrypoints/try_on_routes.py`
- `src/use_cases/try_on/workflow_execution.py`
- `src/adapters/database/sql/business_catalog_repositories.py`
- `src/entrypoints/business_catalog_routes.py`
- `src/use_cases/agents/invocation_service.py`
- `apps/web/src/features/admin/business-catalog-review.tsx`
- `apps/web/src/features/workspace/try-on-workflow.tsx`
- `apps/web/src/lib/api/client.ts`
- `apps/web/src/lib/api/contracts.ts`
- `apps/web/src/app/globals.css`
- several test files and operational scripts.

Recommendation: do not refactor these randomly. Split only when touching a feature area, starting with admin business catalog UI and runtime dependency builders because they have the largest blast radius.

## What Can Still Be Improved Before Billing

Priority 1, useful before billing:

1. Add a production infrastructure readiness gate that explicitly blocks production-like envs when SQL, Redis, S3, auth, billing, provider, and admin tokens are incomplete.
2. Add a focused audit guardrail for active runtime fallback usage: production env must not silently use in-memory repositories/queues/storage for customer workflows.
3. Refresh `docs/04_OWNER_REMAINING_WORK.md` or replace it with an updated owner-facing status document based on current gates and test counts.
4. Add npm audit evidence to the acceptance flow. Previous owner docs mention npm audit findings; current pre-billing gate does not record audit status.
5. Add a small route/action audit script that enumerates active Next routes, verifies README/docs alignment, and rejects missing canonical project routes.

Priority 2, enterprise polish:

1. Decompose the largest active frontend admin page and API client into feature-specific modules.
2. Centralize Python quality tooling in a `pyproject.toml` or equivalent config if we decide to add ruff/mypy.
3. Add a dedicated test to ensure public docs do not contain stale readiness counts after acceptance gates change.
4. Add deployed staging evidence collection output for `/health`, `/ready`, public pages, workspace routes, and admin readiness.

## Recommended Next Step

Implement Priority 1 item 1: a production infrastructure readiness gate.

This is the highest-value next no-billing task because it prevents a dangerous state after billing is enabled: the app looking ready while any production-critical adapter still falls back to local/in-memory/sandbox behavior.

Expected scope:

- new `scripts/production_infrastructure_readiness_gate.py`;
- tests for fail-closed production checks;
- integration into post-billing acceptance gate;
- runbook update;
- no changes to business behavior.

## Current Conclusion

The project is locally ready for pre-billing client testing and prepared for post-billing acceptance. It is not yet ready for real paid customer production until external billing/auth/provider activation and live acceptance are completed.

The safest next work before billing is not adding more product features. It is adding a strict production infrastructure gate, then refreshing owner docs so the team follows the current truth instead of older status snapshots.
