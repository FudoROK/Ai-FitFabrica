# Post-Billing Live Acceptance Report Template

Copy this template to `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md` after billing/auth/provider access is restored.

## Environment

- Date:
- Operator:
- Backend URL:
- Frontend URL:
- Git commit:
- Billing mode:
- Auth provider:
- LLM provider:
- Image generation/editing provider:
- Marketplace/search sources enabled:

## Required Preflight

```powershell
.venv\Scripts\python.exe scripts/post_billing_acceptance_gate.py `
  --api-base-url "https://api.fit.aisoulfabrica.com" `
  --status-token "<STATUS_ENDPOINT_TOKEN>" `
  --require-ready

.venv\Scripts\python.exe scripts/platform_foundation_smoke.py --require-ready
.venv\Scripts\python.exe scripts/business_catalog_search_index_readiness.py --require-db
.venv\Scripts\python.exe scripts/try_on_real_activation_smoke.py --require-ready
.venv\Scripts\python.exe scripts/business_catalog_staging_smoke.py
```

## Global Pass Criteria

- `/ready` has no blockers.
- Production auth creates and reads a real session.
- Billing core records estimates, holds, final charges, refunds, and ledger entries on backend only.
- Frontend never calls model/provider APIs directly.
- Paid provider failures return structured backend errors.
- User-visible broken image/content results are rejected, repaired, retried, or kept hidden.
- Admin routes require bearer-token or production admin auth.

## B2C Acceptance

### Public Entry

- Routes: `/`, `/for-you`, `/pricing`, `/contact`, `/login`.
- Actions:
  - Submit contact/demo request.
  - Sign in with production auth.
- Expected:
  - Public pages return HTTP `200`.
  - Contact/demo request persists in SQL.
  - Auth creates a backend-owned session.
- Result:
  - Status:
  - Evidence:
  - Notes:

### Try-On

- Routes: `/workspace/try-on/new`, `/workspace/try-on/result`.
- Actions:
  - Upload valid human photo.
  - Upload valid garment photo.
  - Submit try-on job.
  - Wait for worker result.
  - Inspect quality verifier and credit ledger.
- Expected:
  - Job is persisted in SQL.
  - Media is stored in object storage.
  - Live provider generation runs only through backend.
  - Quality verifier pass/repair/retry/reject decision is stored.
  - Credits are charged or refunded by backend policy only.
- Result:
  - Status:
  - Job id:
  - Credit ledger id:
  - Evidence:
  - Notes:

### Similar Search

- Route: `/workspace/similar-search`.
- Actions:
  - Submit garment photo search.
  - Open at least one result link.
  - Verify click event persistence.
- Expected:
  - Search uses approved source connectors only.
  - Results are ranked by backend.
  - Click events are stored.
  - No hidden scraping or browser-side marketplace logic is used.
- Result:
  - Status:
  - Search id:
  - Evidence:
  - Notes:

### Outfit Builder

- Route: `/workspace/outfit-builder`.
- Actions:
  - Create outfit request.
  - Verify generated recommendation payload.
- Expected:
  - Backend owns request state.
  - Provider output is structured and validated.
  - Credits are recorded by backend.
- Result:
  - Status:
  - Request id:
  - Evidence:
  - Notes:

## B2B Acceptance

### Business Catalog

- Routes: `/workspace/business-catalog`, `/workspace/business-catalog/new`, `/workspace/business-catalog/import`.
- Actions:
  - Save merchant profile.
  - Create product.
  - Upload image.
  - Import CSV.
  - Submit product to review.
- Expected:
  - Merchant/product/import state persists in SQL.
  - Image metadata and object storage references are valid.
  - Validation errors are structured.
- Result:
  - Status:
  - Product id:
  - Import id:
  - Evidence:
  - Notes:

### Product Card

- Route: `/workspace/product-card`.
- Actions:
  - Create product card job.
  - Verify garment analysis.
  - Verify generated title/description/attributes.
- Expected:
  - Job and result persist in SQL.
  - Live provider output is validated before display.
  - Credits are charged by backend only.
- Result:
  - Status:
  - Job id:
  - Evidence:
  - Notes:

### Content Package

- Route: `/workspace/content-package`.
- Actions:
  - Create content package job.
  - Verify artifact metadata and generated copy.
- Expected:
  - Job state is backend-owned.
  - Generated artifacts are stored and retrievable.
  - Errors are visible and structured.
- Result:
  - Status:
  - Job id:
  - Evidence:
  - Notes:

### Pricing

- Route: `/workspace/projects`.
- Actions:
  - Create pricing job.
  - Verify comparable products/source data.
  - Verify pricing explanation.
- Expected:
  - Pricing source is explicit and approved.
  - Backend returns min/avg/premium range.
  - Credits are recorded by backend.
- Result:
  - Status:
  - Job id:
  - Evidence:
  - Notes:

### Admin Review

- Routes: `/admin/readiness`, `/admin/business-catalog`, `/admin/taxonomy`, `/admin/business-accounts`.
- Actions:
  - Open readiness dashboard with token/auth.
  - Approve one pending catalog product or discovery candidate.
  - Reject one pending item with reason.
  - Archive one item.
  - Run category validation where enabled.
- Expected:
  - Unauthorized requests fail closed.
  - Approve/reject/archive are persisted in SQL.
  - Admin UI does not expose unsafe role/id headers.
- Result:
  - Status:
  - Evidence:
  - Notes:

## Final Decision

- Overall status: `passed` / `blocked`
- Blocking issues:
- Follow-up commits:
- Production launch decision:
