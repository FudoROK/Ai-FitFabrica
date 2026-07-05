# Pre-Billing Client Acceptance Checklist

Use this checklist after local gates pass and before enabling billing/auth/live providers. It verifies that the product is ready for client testing except for the external systems that cannot be completed before activation.

## Required Commands

Run locally from the repository root:

```powershell
.venv\Scripts\python.exe scripts/client_readiness_gate.py
.venv\Scripts\python.exe scripts/auth_readiness_gate.py
.venv\Scripts\python.exe scripts/billing_readiness_gate.py
.venv\Scripts\python.exe scripts/no_billing_acceptance_gate.py --full-backend
```

Run against deployed staging after backend and frontend deploy:

```powershell
.venv\Scripts\python.exe scripts/staging_no_billing_smoke.py `
  --api-base-url "https://api.fit.aisoulfabrica.com" `
  --web-base-url "https://fit.aisoulfabrica.com" `
  --status-token "<STATUS_ENDPOINT_TOKEN>"
```

## Pass Criteria

- `client_readiness_gate` returns `readiness_status=ready` and no failed flow checks.
- `auth_readiness_gate` returns `readiness_status=ready` with `AUTH_PROVIDER=disabled` and fail-closed sign-in behavior.
- `billing_readiness_gate` returns `readiness_status=ready` with `BILLING_CORE_ENABLED=false` and backend-owned ledger behavior.
- `no_billing_acceptance_gate.py --full-backend` returns `readiness_status=ready`.
- `staging_no_billing_smoke.py` returns `readiness_status=ready` after deploy.
- Frontend routes return HTTP `200` and render nonblank B2C/B2B pages.
- Backend routes return structured success or intentional fail-closed errors.
- No test path calls paid AI/provider workflows.
- No frontend code calculates credits, billing, orchestration, retry, or AI decisions.

## Blocked until billing/auth/provider activation

- Production sign-in and session creation.
- Real credit charging, refunds, top-up, and invoices.
- Live Try-On generation quality acceptance.
- Live Product Card AI quality acceptance.
- Live Similar Search with approved marketplace/search sources.
- Browser acceptance that requires paid provider output.

## B2C Flows

### b2c_public_entry

- UI routes: `/`, `/for-you`, `/login`, `/contact`.
- Backend: `POST /demo-request`, `POST /auth/sign-in`.
- Before billing: public pages open, contact/demo request persists to backend SQL, sign-in fails closed with structured auth-not-configured response.
- Pass criteria: no placeholder links, forms submit to backend, no fake OAuth or fake session state.
- Blocked until billing/auth/provider activation: real authentication provider and customer session creation.

### b2c_try_on

- UI routes: `/workspace/new-fitting`, `/workspace/try-on/new`, `/workspace/try-on/result`.
- Backend: `POST /api/try-on/jobs`.
- Before billing: upload UI, DTO creation, validation, SQL job persistence, async lifecycle, sandbox/no-paid generation contour, result shell, quality/repair contract tests.
- Pass criteria: invalid uploads are rejected, backend owns job state, browser never calls AI provider directly.
- Blocked until billing/auth/provider activation: live generation quality, paid verifier/repair acceptance, final customer charging.

### b2c_similar_search

- UI route: `/workspace/similar-search`.
- Backend: `POST /api/similar-search`, `POST /api/similar-search/garment-photo`, click event tracking.
- Before billing: query/photo request contract, ranking logic, click event persistence, no hidden scraping.
- Pass criteria: route renders, backend returns structured results or safe empty/error state, events are backend-owned.
- Blocked until billing/auth/provider activation: approved live marketplace/search source coverage and paid provider-dependent image analysis.

### b2c_outfit_builder

- UI route: `/workspace/outfit-builder`.
- Backend: `/api/workspace/outfit-builder/requests`.
- Before billing: request creation/status contract and frontend states are available without provider calls.
- Pass criteria: page renders with loading/error/empty/success states and backend-owned request state.
- Blocked until billing/auth/provider activation: live stylist/provider output and any charged recommendation flow.

## B2B Flows

### b2b_business_catalog

- UI routes: `/workspace/business-catalog`, `/workspace/business-catalog/new`, `/workspace/business-catalog/import`.
- Backend: `/api/business/merchant`, `/api/business/products`, `/api/business/catalog-imports`.
- Before billing: merchant/product create/list, image metadata, CSV import, submit-to-review, SQL persistence.
- Pass criteria: catalog data survives repository re-init, validation errors are structured, no frontend business rules replace backend decisions.
- Blocked until billing/auth/provider activation: paid enrichment and marketplace publishing that depends on external credentials.

### b2b_product_card

- UI route: `/workspace/product-card`.
- Backend: `POST /api/product-cards`, product-card result and garment-analysis endpoints.
- Before billing: product card job creation, SQL persistence, garment analysis contract, safe non-paid generation adapter.
- Pass criteria: job lifecycle is backend-owned, result/analysis endpoints are typed, frontend handles pending/error/empty states.
- Blocked until billing/auth/provider activation: live AI copy/image quality acceptance and paid content generation.

### b2b_content_package

- UI route: `/workspace/content-package`.
- Backend: `POST /api/content-packages`.
- Before billing: content package job contract, SQL persistence, artifact metadata, frontend action wiring.
- Pass criteria: page actions call backend, errors are visible, no hardcoded final content is presented as production output.
- Blocked until billing/auth/provider activation: live provider content package quality acceptance and charging.

### b2b_pricing

- UI route: `/workspace/projects` for pricing-job visibility and project workflow access.
- Backend: `POST /api/pricing-jobs`.
- Before billing: pricing query preparation, ranking, SQL job persistence, provider-neutral workflow contract.
- Pass criteria: pricing output is backend-owned and uses configured data sources, frontend only displays returned DTOs.
- Blocked until billing/auth/provider activation: live comparable product source coverage and charged pricing workflows.

### b2b_admin_review

- UI routes: `/admin/readiness`, `/admin/business-catalog`, `/admin/taxonomy`, `/admin/business-accounts`.
- Backend: `/api/admin/business-catalog`, `/api/admin/taxonomy`, `/api/admin/costs`.
- Before billing: admin pages are feature-flagged, token-authenticated backend routes fail closed, review/approve/reject/archive flows are SQL-backed.
- Pass criteria: admin frontend requests bearer token, unsafe header auth remains disabled, review actions return structured responses.
- Blocked until billing/auth/provider activation: final operator sign-in model and live provider-driven category validation.

## Final Pre-Billing Decision

If all local and staging no-billing gates pass, the project is ready to enable billing/auth/provider access. Do not expose the product to real customers until post-billing acceptance clears the external blockers above.
