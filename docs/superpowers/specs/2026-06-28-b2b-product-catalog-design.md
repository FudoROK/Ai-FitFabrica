# B2B Product Catalog And Business Cabinet Design

## Goal

Build the enterprise foundation for business clients to manage their store profile, product catalog, product media, prices, city/country availability, delivery metadata, and review status inside AI FitFabrica.

This is the foundation for:

- B2B Product Card generation;
- B2B content packages;
- local similar/cheaper search;
- future marketplace connectors;
- future Instagram merchant directory;
- pricing and competitor analysis.

## Product Decision

We do not start from external marketplace scraping.

The first reliable source of searchable products must be our own backend-owned catalog:

```text
Business client
-> uploads / imports products
-> backend validates and persists catalog data
-> optional admin review
-> product becomes searchable
-> similar/cheaper search can use trusted local catalog first
```

External marketplaces and Instagram become later connectors. They must feed normalized catalog records through approved APIs, partner feeds, seller account integrations, or admin-approved merchant records. Hidden scraping is not allowed.

## User Roles

### Business Owner

Can manage only their own business profile, stores, products, imports, product photos, prices, and catalog status.

### Admin

Can review submitted stores/products, approve or reject catalog visibility, inspect import errors, and manage source trust.

### B2C User

Can search and view active approved offers, filtered/ranked by location, similarity, price, and delivery.

## Scope

### In Scope

- Business merchant/store profile.
- Product catalog domain model.
- Product photos and media metadata.
- Manual product create/edit flow.
- CSV/Excel import pipeline.
- Import validation with row-level errors.
- Product statuses: draft, submitted, active, rejected, archived.
- Admin review queue foundation.
- Geo fields: country, city, delivery regions.
- Offer fields: price, currency, availability, URL.
- Backend-owned APIs.
- Frontend business catalog pages.
- Tests and documentation.

### Out Of Scope For This Plan

- Direct Kaspi/Wildberries seller account integration.
- Instagram Graph API integration.
- Public marketplace-wide search.
- Automatic scraping.
- Automatic product approval without policy.
- Real visual similarity embeddings for catalog items.
- Full competitor analysis.

These are later plans built on top of this catalog foundation.

## Architecture

The catalog follows the existing backend-first, hexagonal architecture:

```text
Next.js workspace UI
-> typed API client
-> FastAPI routes
-> use_cases/business_catalog
-> domain/business_catalog
-> SQL repository + object storage
-> optional admin review
```

Frontend remains a thin client. It does not decide approval, visibility, pricing policy, credits, source trust, or search ranking.

## Core Domain Objects

### BusinessMerchant

Represents one business seller profile.

Required fields:

- merchant_id;
- owner_id;
- display_name;
- legal_name optional;
- country_code;
- city;
- contact_email optional;
- instagram_url optional;
- website_url optional;
- status: draft, submitted, active, suspended;
- created_at;
- updated_at.

### BusinessProduct

Represents one seller-owned product.

Required fields:

- product_id;
- merchant_id;
- owner_id;
- title;
- category;
- description optional;
- country_code;
- city;
- status: draft, submitted, active, rejected, archived;
- review_status: not_required, pending, approved, rejected;
- source_type: manual, csv_import, excel_import, partner_feed, admin_created;
- created_at;
- updated_at.

### BusinessProductImage

Represents one uploaded product image.

Required fields:

- image_id;
- product_id;
- object_key;
- content_type;
- size_bytes;
- sha256;
- role: primary, gallery, source, generated;
- sort_order;
- created_at.

### BusinessProductOffer

Represents sellable offer metadata.

Required fields:

- offer_id;
- product_id;
- price_amount;
- currency;
- availability: in_stock, out_of_stock, preorder, unknown;
- product_url optional;
- delivery_regions;
- updated_at.

### CatalogImportJob

Represents CSV/Excel import.

Required fields:

- import_id;
- merchant_id;
- owner_id;
- filename;
- status: uploaded, validating, completed, completed_with_errors, failed;
- total_rows;
- accepted_rows;
- rejected_rows;
- error_summary;
- created_at;
- completed_at optional.

### CatalogImportRowError

Represents row-level validation error.

Required fields:

- import_id;
- row_number;
- field_name;
- safe_code;
- message.

## API Contracts

### Merchant

- `GET /api/business/merchant`
- `POST /api/business/merchant`
- `PATCH /api/business/merchant`

### Products

- `GET /api/business/products`
- `POST /api/business/products`
- `GET /api/business/products/{product_id}`
- `PATCH /api/business/products/{product_id}`
- `POST /api/business/products/{product_id}/submit`
- `POST /api/business/products/{product_id}/archive`

### Product Images

- `POST /api/business/products/{product_id}/images`
- `DELETE /api/business/products/{product_id}/images/{image_id}`

### Import

- `POST /api/business/catalog-imports`
- `GET /api/business/catalog-imports/{import_id}`
- `GET /api/business/catalog-imports/{import_id}/errors`

### Admin Review

- `GET /api/admin/business-catalog/review-queue`
- `POST /api/admin/business-catalog/products/{product_id}/approve`
- `POST /api/admin/business-catalog/products/{product_id}/reject`

Admin routes must be disabled unless admin auth/config is enabled.

## Validation Rules

Product creation requires:

- title;
- category;
- city;
- country_code;
- price_amount;
- currency;
- at least one primary image before submit;
- product URL if the product is intended for public search.

CSV/Excel import must validate:

- required columns;
- row count limit;
- file size limit;
- supported content type;
- safe URL format;
- price format;
- currency;
- city/country;
- duplicate SKU/product URL within same merchant;
- image URLs are accepted only as metadata in first version, not automatically downloaded.

## Status Rules

Draft products are visible only to the business owner.

Submitted products enter review when the source is new or untrusted.

Active products can be used by internal similar search and shown to users.

Rejected products remain visible to the owner with reasons.

Archived products are hidden from search but retained for audit/history.

## Geo Ranking Foundation

Catalog records must store:

- country_code;
- city;
- delivery_regions.

Later search ranking will use:

```text
same city
-> same country
-> delivery available to user city
-> price
-> visual/text similarity
-> source trust
-> freshness
```

This plan stores the data needed for that ranking but does not implement full external marketplace search.

## Frontend Pages

### `/workspace/business-catalog`

Main business product catalog page:

- merchant summary;
- product list;
- filters by status;
- create product CTA;
- import CTA;
- empty state.

### `/workspace/business-catalog/new`

Manual product form:

- title;
- category;
- description;
- price;
- currency;
- country;
- city;
- delivery regions;
- product URL;
- image upload;
- validation states;
- save draft;
- submit for review.

### `/workspace/business-catalog/import`

Import page:

- upload CSV/Excel;
- show required columns;
- validate file;
- show import status;
- show row-level errors.

### `/admin/business-catalog`

Admin review page:

- pending products;
- merchant;
- city/country;
- image preview;
- approve/reject;
- rejection reason.

## Integration With Existing Product Card

Product Card jobs can later be linked to catalog products:

```text
BusinessProduct
-> Product Card generation
-> generated title/description/content
-> save product card version
-> optionally update catalog product fields after owner approval
```

Product Card Agent must not mutate catalog directly.

## Integration With Similar Search

Similar Search should later read active approved catalog products and offers.

Existing `src/domain/similar_search.py` and SQL catalog models can be extended or mapped to the new business catalog tables.

This design prefers a dedicated business catalog domain first, then a projection into search/catalog offer records. That avoids mixing seller-owned draft data with public searchable offers.

## Security

- Owner can access only their own merchant/products/imports.
- Admin review requires admin auth/config.
- Product images go through backend object storage.
- Frontend never gets provider credentials.
- Import files are validated before processing.
- URLs are stored as data; backend does not scrape them.

## Testing Strategy

Backend:

- domain model validation;
- service create/update/submit;
- SQL migration/repository;
- route tests;
- import parser validation;
- admin review;
- ownership guardrails;
- search projection contract.

Frontend:

- typed API client contracts;
- business catalog page;
- manual product form validation;
- import page states;
- locked/admin-only actions;
- lint/typecheck/build.

## Acceptance Criteria

- Business user can create merchant profile.
- Business user can add product manually.
- Business user can upload primary product image.
- Business user can submit product for review.
- Admin can approve/reject product.
- Approved product becomes eligible for future search projection.
- CSV/Excel import creates import job and row-level validation report.
- No external scraping exists.
- Frontend remains thin.
- Tests and docs pass.
