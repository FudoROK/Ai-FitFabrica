# Marketplace Discovery Candidates SQL Persistence

## What Changed

Instagram/open-web discovery candidates are now persisted through the backend SQL repository instead of relying on process memory.

The flow remains backend-owned:

1. Approved discovery adapters produce `MarketplaceDiscoveryCandidate` records.
2. `MarketplaceCandidateReviewService` saves candidates through a repository port.
3. Runtime/admin wiring uses `SqlMarketplaceCandidateRepository` when `settings.sql_session_factory` is configured.
4. In-memory storage remains only as a local/test fallback when no SQL session factory exists.

This does not enable live scraping or live discovery. It only makes reviewed discovery candidates durable.

## Table

Migration: `alembic/versions/20260702_000025_marketplace_discovery_candidates.py`

Table: `marketplace_discovery_candidates`

Important fields:

- `candidate_id`
- `workspace_id`
- `business_id`
- `connector_kind`
- `source_type`
- `source_url`
- `image_url`
- `media_url`
- `source_title`
- `title`
- `name`
- `brand`
- `source_snippet`
- `platform_hint`
- `category`
- `country_code`
- `city`
- `price_amount`
- `currency`
- `raw_payload_json`
- `metadata_json`
- `status`
- `reviewed_by`
- `rejection_reason`
- `approved_at`
- `rejected_at`
- `created_at`
- `updated_at`

Duplicate protection is enforced by repository lookup on `source_url` plus `workspace_id` and `business_id` scope. The migration also defines `uq_marketplace_discovery_candidates_scope_source_url` for PostgreSQL-level protection when scope values are present.

## Repository Operations

`SqlMarketplaceCandidateRepository` supports:

- create one candidate;
- save candidate batches;
- get by id;
- list with filters for status, source type, category, city, workspace, and business;
- list pending review candidates;
- approve;
- reject with optional reason;
- archive.

Review statuses:

- `pending`
- `approved`
- `rejected`
- `archived`

Legacy `needs_review` remains readable for compatibility with earlier records/tests.

## Admin Endpoints

The admin review API uses SQL persistence when SQL is configured:

- `GET /api/admin/business-catalog/discovery-candidates/pending`
- `GET /api/admin/business-catalog/discovery-candidates`
- `POST /api/admin/business-catalog/discovery-candidates/{candidate_id}/approve`
- `POST /api/admin/business-catalog/discovery-candidates/{candidate_id}/reject`
- `POST /api/admin/business-catalog/discovery-candidates/{candidate_id}/archive`

All endpoints remain behind the existing admin business catalog auth and feature flag.

## Remaining Admin UI Work

The backend is ready for admin UI integration. Remaining UI work:

- add candidate list screen with filters;
- show source URL/media/title/brand/category/city/price fields;
- add approve/reject/archive actions;
- require or optionally collect rejection reason;
- show duplicate/source trust context before approval;
- connect approved candidates to the later enrichment/import flow.
