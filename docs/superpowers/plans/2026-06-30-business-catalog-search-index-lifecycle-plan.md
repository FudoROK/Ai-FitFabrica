# Business Catalog Search Index Lifecycle Plan

**Goal:** Make approved B2B catalog products search-index aware without coupling admin approval to Qdrant/provider availability.

**Decision:** Admin approval is a business lifecycle transition. Search indexing is an asynchronous infrastructure workflow. Approving a product marks it as `active/approved` and sets `search_index_status=pending`. Reindex/worker execution later marks it `indexed` or `failed`.

## Implemented Scope

- [x] Added product search index lifecycle statuses: `not_indexed`, `pending`, `indexed`, `failed`.
- [x] Product approval now marks approved products as `pending` for search indexing.
- [x] Editing an already active/approved product marks the search index as `pending` again.
- [x] SQL persistence now stores `search_index_status`, `search_index_error`, and `search_indexed_at`.
- [x] Added Alembic migration `20260630_000022_business_catalog_search_index_status`.
- [x] Reindex script now marks indexed products as `indexed` after success.
- [x] Reindex script marks products as `failed` if indexing raises an error.
- [x] Frontend typed business catalog contract includes search index fields.
- [x] Business catalog and admin review pages show the search index status.
- [x] Added admin retry endpoint for search indexing failures.
- [x] Added admin UI retry button for `failed` search index records.
- [x] Added admin UI filter by search index status.
- [x] Added automatic operations queue dispatch after admin approve and admin retry.
- [x] Added `business_catalog_search_index` worker handler that executes the shared indexing workflow.

## Follow-Up Scope

- [x] Add background worker dispatch on approval after staging queue policy is finalized.
- [x] Add admin action for retrying failed search indexing.
- [x] Add admin filter by search index status.
- [ ] Add staging smoke for migration + indexing worker after realistic catalog products are loaded.

## Verification

- Backend targeted tests: `29 passed`; retry route/client targeted tests: `4 passed`.
- Web typecheck: passed.
- Web lint: passed.
- Auto-dispatch targeted tests: `30 passed`.
