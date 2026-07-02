# B2B Product Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the enterprise foundation for business clients to manage their own merchant profile, product catalog, product images, prices, geo availability, manual product creation, CSV/Excel import, and admin review.

**Architecture:** Keep the workspace as a thin Next.js client over backend-owned catalog state. Add a dedicated business catalog domain/use-case/API/SQL contour, then project approved catalog records into future similar-search sources instead of mixing drafts with public search data.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, PostgreSQL, object storage, Next.js, React, TypeScript, Tailwind, pytest, frontend lint/typecheck/build.

---

## File Structure

Create:

- `src/domain/business_catalog.py` - pure domain models and enums.
- `src/use_cases/business_catalog/ports.py` - repository and file-storage ports.
- `src/use_cases/business_catalog/service.py` - merchant/product/import/review orchestration.
- `src/use_cases/business_catalog/import_parser.py` - CSV/Excel parsing and row validation.
- `src/adapters/database/sql/business_catalog_models.py` - SQLAlchemy models.
- `src/adapters/database/sql/business_catalog_serialization.py` - SQL/domain mapping.
- `src/adapters/database/sql/business_catalog_repositories.py` - SQL repository.
- `src/entrypoints/business_catalog_routes.py` - business-facing APIs.
- `src/entrypoints/admin_business_catalog_routes.py` - admin review APIs.
- `alembic/versions/20260628_000021_business_catalog.py` - schema migration.
- `apps/web/src/lib/api/business-catalog-contracts.ts` - frontend API types.
- `apps/web/src/features/workspace/business-catalog/` - UI components.
- `apps/web/src/app/(workspace)/workspace/business-catalog/page.tsx`
- `apps/web/src/app/(workspace)/workspace/business-catalog/new/page.tsx`
- `apps/web/src/app/(workspace)/workspace/business-catalog/import/page.tsx`
- `apps/web/src/app/(admin)/admin/business-catalog/page.tsx`

Modify:

- `src/entrypoints/http_routes.py` - include new routers.
- `src/entrypoints/runtime_dependency_contracts.py` - add catalog runtime bundle if needed.
- `src/entrypoints/runtime_dependency_builders.py` - wire service/repository.
- `apps/web/src/lib/api/client.ts` - business catalog methods.
- `apps/web/src/lib/routes/workspace-routes.ts` - add business catalog nav item.
- `apps/web/src/lib/api/contracts.ts` - capabilities if required.
- `src/use_cases/workspace/capability_service.py` - expose business catalog capabilities.
- `docs/01_ACTION_LOG_CHECKLIST.md` - update progress after each gate.
- `docs/03_AGENT_SYSTEM_GUIDE.md` - update only if agent/model behavior changes.

---

## Task 1: Domain Models

**Files:**

- Create: `src/domain/business_catalog.py`
- Test: `tests/test_business_catalog_domain.py`

- [x] **Step 1: Write failing domain tests**

```python
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessProduct,
    BusinessProductOffer,
    BusinessProductStatus,
    ReviewStatus,
)


def test_business_product_requires_core_catalog_fields() -> None:
    product = BusinessProduct(
        product_id="product_1",
        merchant_id="merchant_1",
        owner_id="owner_1",
        title="White oversized shirt",
        category="shirt",
        country_code="KZ",
        city="Almaty",
        status=BusinessProductStatus.DRAFT,
        review_status=ReviewStatus.NOT_REQUIRED,
        source_type="manual",
    )

    assert product.title == "White oversized shirt"
    assert product.country_code == "KZ"
    assert product.city == "Almaty"


def test_business_product_offer_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        BusinessProductOffer(
            offer_id="offer_1",
            product_id="product_1",
            price_amount=Decimal("-1"),
            currency="KZT",
            availability="in_stock",
            delivery_regions=["Almaty"],
        )
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_domain.py -q
```

Expected: import/module missing.

- [x] **Step 3: Implement domain models**

Create strict Pydantic models with enums:

- `BusinessMerchantStatus`;
- `BusinessProductStatus`;
- `ReviewStatus`;
- `ProductImageRole`;
- `ProductAvailability`;
- `BusinessMerchant`;
- `BusinessProduct`;
- `BusinessProductImage`;
- `BusinessProductOffer`;
- `CatalogImportJob`;
- `CatalogImportRowError`.

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_domain.py -q
```

Expected: pass.

---

## Task 2: Use-Case Service And Ports

**Files:**

- Create: `src/use_cases/business_catalog/ports.py`
- Create: `src/use_cases/business_catalog/service.py`
- Create: `src/use_cases/business_catalog/__init__.py`
- Test: `tests/test_business_catalog_service.py`

- [x] **Step 1: Write failing service tests**

Cover:

- create merchant;
- create draft product;
- reject submit without primary image;
- submit product with primary image creates pending review;
- owner cannot access another owner's product.

- [x] **Step 2: Run service tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_service.py -q
```

- [x] **Step 3: Implement ports**

Define:

- `BusinessCatalogRepositoryPort`;
- `BusinessCatalogFileStoragePort`.

Repository methods:

- `save_merchant`;
- `get_merchant_by_owner`;
- `save_product`;
- `get_product`;
- `list_products`;
- `save_product_image`;
- `list_product_images`;
- `save_offer`;
- `get_offer`;
- `save_import_job`;
- `save_import_errors`.

- [x] **Step 4: Implement service**

Service methods:

- `upsert_merchant`;
- `create_product`;
- `update_product`;
- `add_product_image`;
- `submit_product`;
- `archive_product`;
- `list_products`;
- `get_product`;
- `approve_product`;
- `reject_product`.

Rules:

- submit requires owner match;
- submit requires primary image;
- submit requires offer/price;
- approve/reject requires admin actor id;
- no external scraping.

- [x] **Step 5: Run service tests and verify GREEN**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_service.py -q
```

---

## Task 3: SQL Schema And Repository

**Files:**

- Create: `alembic/versions/20260628_000021_business_catalog.py`
- Create: `src/adapters/database/sql/business_catalog_models.py`
- Create: `src/adapters/database/sql/business_catalog_serialization.py`
- Create: `src/adapters/database/sql/business_catalog_repositories.py`
- Modify: `src/adapters/database/sql/__init__.py`
- Test: `tests/test_business_catalog_sql_migration.py`
- Test: `tests/test_business_catalog_sql_repository.py`

- [x] **Step 1: Write failing SQL tests**

Tests must verify:

- tables exist after migration;
- merchant/product/offer/image round trip;
- list products by owner;
- review status persists;
- import job/errors persist.

- [x] **Step 2: Run SQL tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_sql_migration.py tests/test_business_catalog_sql_repository.py -q
```

- [x] **Step 3: Add migration**

Tables:

- `business_merchants`;
- `business_products`;
- `business_product_images`;
- `business_product_offers`;
- `business_catalog_import_jobs`;
- `business_catalog_import_row_errors`.

Indexes:

- owner id;
- merchant id;
- product status;
- review status;
- country/city;
- product URL;
- import id.

- [x] **Step 4: Implement repository**

Use SQLAlchemy patterns from existing product card/workspace repositories.

- [x] **Step 5: Run SQL tests and verify GREEN**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_sql_migration.py tests/test_business_catalog_sql_repository.py -q
```

---

## Task 4: Business API Routes

**Files:**

- Create: `src/entrypoints/business_catalog_routes.py`
- Create: `src/entrypoints/admin_business_catalog_routes.py`
- Modify: `src/entrypoints/http_routes.py`
- Test: `tests/test_business_catalog_routes.py`
- Test: `tests/test_admin_business_catalog_routes.py`

- [x] **Step 1: Write failing route tests**

Cover:

- `GET /api/business/merchant`;
- `POST /api/business/merchant`;
- `GET /api/business/products`;
- `POST /api/business/products`;
- `POST /api/business/products/{product_id}/submit`;
- admin approve/reject disabled by default;
- admin approve/reject requires admin header/config.

- [x] **Step 2: Run route tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_routes.py tests/test_admin_business_catalog_routes.py -q
```

- [x] **Step 3: Implement DTOs and routes**

DTOs must be strict Pydantic models.

Return structured errors:

- `business_catalog_not_found`;
- `business_catalog_forbidden`;
- `business_catalog_validation_failed`;
- `business_catalog_admin_disabled`;
- `business_catalog_submit_blocked`.

- [x] **Step 4: Wire routes in `http_routes.py`**

Include routers with existing API style.

- [x] **Step 5: Run route tests and verify GREEN**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_routes.py tests/test_admin_business_catalog_routes.py -q
```

---

## Task 5: Product Image Upload

**Files:**

- Modify: `src/use_cases/business_catalog/service.py`
- Modify: `src/entrypoints/business_catalog_routes.py`
- Test: `tests/test_business_catalog_image_upload.py`

- [x] **Step 1: Write failing upload tests**

Cover:

- supported file types;
- max file size;
- primary image storage;
- owner access;
- submit blocked without primary image.

- [x] **Step 2: Run upload tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_image_upload.py -q
```

- [x] **Step 3: Implement image upload**

Endpoint:

- `POST /api/business/products/{product_id}/images`

Use object storage through backend only.

- [x] **Step 4: Run upload tests and verify GREEN**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_image_upload.py -q
```

---

## Task 6: CSV/Excel Import

**Files:**

- Create: `src/use_cases/business_catalog/import_parser.py`
- Modify: `src/use_cases/business_catalog/service.py`
- Modify: `src/entrypoints/business_catalog_routes.py`
- Test: `tests/test_business_catalog_import_parser.py`
- Test: `tests/test_business_catalog_import_routes.py`

- [x] **Step 1: Write failing parser tests**

Required columns:

```text
title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions
```

Validate:

- missing required columns;
- invalid price;
- invalid currency;
- invalid URL;
- row-level errors;
- partial success.

- [x] **Step 2: Run parser tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_import_parser.py -q
```

- [x] **Step 3: Implement CSV parser**

Start with CSV. Excel can be parsed after CSV through the same normalized row model.

- [x] **Step 4: Implement import endpoint**

Endpoint:

- `POST /api/business/catalog-imports`
- `GET /api/business/catalog-imports/{import_id}`
- `GET /api/business/catalog-imports/{import_id}/errors`

- [x] **Step 5: Run import tests and verify GREEN**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_import_parser.py tests/test_business_catalog_import_routes.py -q
```

---

## Task 7: Frontend API Client

**Files:**

- Create: `apps/web/src/lib/api/business-catalog-contracts.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Test: `tests/test_business_catalog_frontend_contracts.py`

- [x] **Step 1: Write failing contract tests**

Check frontend files contain:

- typed merchant response;
- typed product response;
- create product payload;
- import status response;
- no `any`.

- [x] **Step 2: Run frontend contract tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_frontend_contracts.py -q
```

- [x] **Step 3: Implement TypeScript contracts and client methods**

Methods:

- `getBusinessMerchant`;
- `saveBusinessMerchant`;
- `listBusinessProducts`;
- `createBusinessProduct`;
- `submitBusinessProduct`;
- `uploadBusinessProductImage`;
- `createBusinessCatalogImport`;
- `getBusinessCatalogImport`;
- `getBusinessCatalogImportErrors`.

- [x] **Step 4: Run contract tests and verify GREEN**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_frontend_contracts.py -q
```

---

## Task 8: Workspace UI

**Files:**

- Create: `apps/web/src/features/workspace/business-catalog/business-catalog-page.tsx`
- Create: `apps/web/src/features/workspace/business-catalog/business-product-form.tsx`
- Create: `apps/web/src/features/workspace/business-catalog/business-catalog-import-page.tsx`
- Create: `apps/web/src/app/(workspace)/workspace/business-catalog/page.tsx`
- Create: `apps/web/src/app/(workspace)/workspace/business-catalog/new/page.tsx`
- Create: `apps/web/src/app/(workspace)/workspace/business-catalog/import/page.tsx`
- Modify: `apps/web/src/lib/routes/workspace-routes.ts`
- Test: `tests/test_workspace_business_catalog_page.py`

- [x] **Step 1: Write failing page tests**

Static tests must check:

- route files exist;
- visible labels exist;
- upload validation text exists;
- loading/error/empty states exist;
- disabled submit during invalid form;
- no fake marketplace publish action.

- [x] **Step 2: Run page tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_workspace_business_catalog_page.py -q
```

- [x] **Step 3: Implement page components**

Keep UI aligned with current workspace visual language.

Required states:

- loading;
- empty;
- error;
- validation errors;
- success;
- disabled during submit.

- [x] **Step 4: Run page tests and frontend checks**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_workspace_business_catalog_page.py -q
cd apps/web
npm run lint
npm run typecheck
npm run build
```

---

## Task 9: Admin Review UI

**Files:**

- Create: `apps/web/src/features/admin/business-catalog-review.tsx`
- Create: `apps/web/src/app/(admin)/admin/business-catalog/page.tsx`
- Test: `tests/test_admin_business_catalog_page.py`

- [x] **Step 1: Write failing admin page tests**

Check:

- review queue page exists;
- approve/reject actions are typed;
- admin disabled/forbidden states are visible;
- rejection reason field exists.

- [x] **Step 2: Run admin page tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_admin_business_catalog_page.py -q
```

- [x] **Step 3: Implement admin review page**

Admin page must not be linked as public workspace action unless admin capability is present.

- [x] **Step 4: Run page tests and frontend checks**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_admin_business_catalog_page.py -q
cd apps/web
npm run lint
npm run typecheck
npm run build
```

---

## Task 10: Search Projection Contract

**Files:**

- Create: `src/use_cases/business_catalog/search_projection.py`
- Test: `tests/test_business_catalog_search_projection.py`

- [x] **Step 1: Write failing projection tests**

Check:

- only active approved products project to search;
- draft/rejected/archived products do not project;
- city/country/delivery fields are preserved;
- price/currency are preserved.

- [x] **Step 2: Run projection tests and verify RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_search_projection.py -q
```

- [x] **Step 3: Implement projection**

Return records compatible with future similar-search hydration, without mixing draft seller data into public search.

- [x] **Step 4: Run projection tests and verify GREEN**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_search_projection.py -q
```

---

## Task 11: Reliability And Scale Hardening

**Purpose:** Apply the practical lessons from Kleppmann-style scalable systems before the catalog becomes a high-volume B2B and marketplace-search surface.

This is not a premature rewrite into distributed complexity. This task adds the seams and tests that let the system grow safely: tenant isolation, hot-account handling, idempotency, backpressure, and controlled failure testing.

**Files:**

- Create: `src/use_cases/business_catalog/tenant_partitioning.py`
- Create: `src/use_cases/business_catalog/tier_admin.py`
- Create: `src/use_cases/business_catalog/idempotency.py`
- Create: `tests/test_business_catalog_tenant_partitioning.py`
- Create: `tests/test_admin_business_catalog_tier_routes.py`
- Create: `tests/test_admin_business_accounts_page.py`
- Create: `tests/test_business_catalog_import_idempotency.py`
- Create: `tests/test_business_catalog_failure_injection.py`
- Modify: `src/use_cases/business_catalog/service.py`
- Modify: `src/entrypoints/business_catalog_routes.py`
- Modify: `docs/accepted_risks.md`

- [x] **Step 1: Write failing tenant partition and tier recommendation tests**

Check:

- every product/import/image storage key can be derived from `owner_id`, `merchant_id`, and `product_id`;
- default merchants use assigned tier `standard` and shared partitions;
- assigned tier `large` routes a merchant to dedicated queue/storage/rate-limit buckets without changing domain models;
- backend can recommend `standard` or `large` from catalog metrics;
- recommendation never changes the effective partition by itself;
- partitioning does not expose whether another merchant exists.

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_tenant_partitioning.py -q
```

- [x] **Step 2: Implement tenant partitioning and recommendation policy**

Add a small backend policy that returns:

- `tenant_key`;
- `queue_partition`;
- `storage_prefix`;
- `rate_limit_bucket`;
- `assigned_tier`;
- `recommended_tier`;
- `recommendation_reasons`;
- `hot_account_mode`.

Rules:

- default partition is deterministic from `owner_id`;
- only admin-assigned tier changes effective queue/storage/rate-limit routing;
- backend recommendations are advisory until an admin confirms them;
- explicit `large` assignment routes a merchant to a dedicated queue/storage prefix later;
- no frontend decision participates in partitioning.

- [x] **Step 2a: Add admin tier API and UI**

Add backend/admin surface for semi-automatic tier management:

- `GET /api/admin/business-catalog/merchants/tiers` returns merchant tier cards, current assigned tier, recommendation, metrics snapshot and reason codes;
- `POST /api/admin/business-catalog/merchants/{merchant_id}/tier` assigns `standard` or `large` with explicit admin reason;
- `/admin/business-accounts` shows current tier, recommended tier, reason codes and manual assignment actions;
- no automatic promotion/demotion without admin actor id and audit-ready reason.

- [x] **Step 3: Write failing idempotency tests**

Check:

- retrying CSV import with the same idempotency key does not duplicate accepted products;
- retrying product image upload with the same idempotency key does not duplicate image metadata;
- retrying submit-to-review does not create multiple review transitions;
- failed validation responses are safe to retry.

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_import_idempotency.py -q
```

- [x] **Step 4: Implement backend idempotency contract**

Add backend-owned idempotency support for:

- `POST /api/business/catalog-imports`;
- `POST /api/business/products/{product_id}/images`;
- `POST /api/business/products/{product_id}/submit`.

Use an adapter/port boundary so Redis/PostgreSQL idempotency storage can be swapped later.

- [x] **Step 5: Write failing failure-injection tests**

Simulate controlled failures:

- object storage save fails after validation;
- repository save fails after object storage save;
- repository save succeeds but import row error save fails;
- backend returns structured errors, not silent failures;
- credits are not charged by catalog import/upload failures.

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_failure_injection.py -q
```

- [x] **Step 6: Implement fail-closed and compensating behavior**

Add structured errors and cleanup hooks:

- storage failure -> no product image metadata;
- metadata failure after storage -> return structured failure and record cleanup requirement;
- import partial failure -> persist job as failed or completed_with_errors with explicit reason;
- no silent `except`;
- no duplicate products on retry.

- [x] **Step 7: Add backpressure and degraded-mode rules**

Before enabling high-volume imports:

- define max CSV rows per import for the current tier;
- return structured `business_catalog_backpressure` when import is too large or queue/storage is unavailable;
- catalog read/list pages continue working when AI/generation providers are unavailable;
- AI/model outage must not block merchant/product CRUD.

- [x] **Step 8: Run reliability verification**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_tenant_partitioning.py tests/test_business_catalog_import_idempotency.py tests/test_business_catalog_failure_injection.py -q
.venv\Scripts\python.exe -m pytest tests/test_business_catalog_domain.py tests/test_business_catalog_service.py tests/test_business_catalog_sql_repository.py tests/test_business_catalog_routes.py tests/test_business_catalog_import_routes.py tests/test_business_catalog_image_upload.py -q
```

Expected:

- tenant partition tests pass;
- idempotency tests pass;
- failure-injection tests pass;
- existing catalog flow remains green.

---

## Task 12: Documentation And Verification

**Files:**

- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Modify: `docs/02_TECHNICAL_PROJECT_MAP.md`
- Modify: `docs/backend_file_catalog.md`
- Modify: `docs/frontend_file_catalog.md`
- Modify: `docs/04_OWNER_REMAINING_WORK.md`

- [x] **Step 1: Update docs**

Record:

- B2B catalog scope;
- API routes;
- admin review status;
- import status;
- search projection status;
- tenant/hot-account partitioning status;
- idempotency/backpressure status;
- controlled failure-injection status;
- what remains for marketplace/Instagram connectors.

- [x] **Step 2: Run backend verification**

```powershell
.venv\Scripts\python.exe scripts/check_architecture.py
.venv\Scripts\python.exe -m compileall src scripts
.venv\Scripts\python.exe -m pytest -q
```

Expected:

- architecture pass;
- compileall pass;
- backend tests pass.

- [x] **Step 3: Run frontend verification**

```powershell
cd apps/web
npm run lint
npm run typecheck
npm run build
```

Expected:

- lint pass;
- typecheck pass;
- build pass.

---

## Rollout Notes

VM is not required for local implementation until backend routes and frontend are ready.

VM/staging is required later for:

- SQL migration smoke;
- object storage upload smoke;
- CSV import smoke;
- frontend/backend deployed route smoke.

Do not enable marketplace/Instagram external search in this plan.

Do not add hidden scraping.

Do not auto-approve unknown merchants/products without admin or trusted-source policy.
