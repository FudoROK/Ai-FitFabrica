# AI FitFabrica Backend File Catalog

Last updated: `2026-06-14`

This catalog describes the active backend modules in `src`. It is a working map of the current codebase, not a file-by-file dump.

## 1. Backend Root

Main zones:

- `src/main.py` - FastAPI bootstrap
- `src/worker.py` - worker bootstrap
- `src/settings.py` - typed runtime settings facade
- `src/entrypoints` - HTTP boundary and composition root
- `src/use_cases` - application workflows
- `src/domain` - typed business models
- `src/adapters` - infrastructure adapters
- `src/runtime_agents` - runtime-owned dialog and memory tasks
- `src/adk_agents` - product-agent roots

## 2. Entry Points

Key route aggregation:

- `src/entrypoints/http_routes.py`

Mounted route modules:

- `status_routes.py`
- `workspace_routes.py`
- `workspace_capability_routes.py`
- `workspace_profile_routes.py`
- `workspace_integration_routes.py`
- `outfit_builder_routes.py`
- `credits_routes.py`
- `try_on_routes.py`
- `similar_search_routes.py`
- `product_card_routes.py`
- `content_package_routes.py`
- `pricing_routes.py`

## 3. Runtime Composition Root

Stable public runtime entrypoint:

- `src/entrypoints/runtime_dependencies.py`

Supporting modules:

- `src/entrypoints/runtime_dependency_contracts.py`
- `src/entrypoints/runtime_dependency_builders.py`
- `src/entrypoints/runtime_dependency_foundation_builders.py`
- `src/entrypoints/runtime_dependency_workflow_builders.py`
- `src/entrypoints/runtime_dependency_operations_builders.py`
- `src/entrypoints/runtime_dependency_cache.py`
- `src/entrypoints/runtime_dependency_lazy_factories.py`

## 4. Workspace Backend

Workspace-facing domain and persistence:

- `src/domain/workspace.py`
- `src/domain/workspace_state.py`
- `src/adapters/workspace`
- `src/adapters/database/sql/workspace_state_models.py`
- `src/adapters/database/sql/workspace_state_repositories.py`

Workspace use cases:

- `src/use_cases/workspace/workspace_bootstrap_service.py`
- `src/use_cases/workspace/business_profile_service.py`
- `src/use_cases/workspace/capability_service.py`
- `src/use_cases/workspace/integration_service.py`
- `src/use_cases/workspace/outfit_builder_service.py`

## 5. Core Workflows

Try-On:

- domain: `src/domain/try_on.py`
- Human Identity domain snapshot: `src/domain/try_on_human_identity.py`
- use case: `src/use_cases/try_on`
- backend continuation policy: `src/use_cases/try_on/human_identity_policy.py`
- canonical Human Identity adapter: `src/adapters/agents/human_identity_analysis.py`
- routes: `src/entrypoints/try_on_routes.py`
- SQL repo: `src/adapters/database/sql/try_on_repositories.py`
- SQL analysis migration: `alembic/versions/20260614_000012_try_on_human_identity_analysis.py`
- parallel analysis bundle: `src/use_cases/try_on/analysis_bundle_service.py`
- Try-On Garment Identity adapter: `src/adapters/agents/try_on_garment_identity_analysis.py`
- Try-On Material / Texture adapter: `src/adapters/agents/try_on_material_texture_analysis.py`
- analysis bundle migration: `alembic/versions/20260615_000015_try_on_analysis_bundle.py`
- typed instruction domain snapshot: `src/domain/try_on_instruction.py`
- provider-neutral Try-On Instruction adapter: `src/adapters/agents/try_on_instruction.py`
- instruction persistence migration: `alembic/versions/20260615_000016_try_on_instruction.py`
- media storage: `src/adapters/storage/media_storage.py`
- no legacy Firestore/GCS Try-On storage adapters remain in the active tree

Similar Search:

- domain: `src/domain/similar_search.py`
- use case: `src/use_cases/similar_search`
- routes: `src/entrypoints/similar_search_routes.py`
- SQL/catalog repo: `src/adapters/database/sql/catalog_repositories.py`
- vector retrieval: `src/adapters/vector/qdrant_retriever.py`

Product Card:

- domain: `src/domain/product_card.py`
- use case: `src/use_cases/product_card`
- safe generation errors: `src/use_cases/product_card/generation_errors.py`
- routes: `src/entrypoints/product_card_routes.py`
- isolated runtime composition: `src/entrypoints/runtime_dependency_product_card_builder.py`
- canonical Garment Identity analysis adapter: `src/adapters/agents/garment_identity_analysis.py`
- canonical agent generation adapter: `src/adapters/agents/product_card_generation.py`
- deterministic test adapters: `src/adapters/agents/deterministic_garment_identity_analysis.py`, `src/adapters/product_card/fake_generation.py`
- SQL repo: `src/adapters/database/sql/product_card_repositories.py`
- persisted analysis migration: `alembic/versions/20260615_000014_product_card_garment_analysis.py`

Content Package:

- domain: `src/domain/content_package.py`
- use case: `src/use_cases/content_package`
- routes: `src/entrypoints/content_package_routes.py`
- SQL repo: `src/adapters/database/sql/content_package_repositories.py`

Pricing:

- domain: `src/domain/pricing.py`
- use case: `src/use_cases/pricing`
- routes: `src/entrypoints/pricing_routes.py`
- SQL repo: `src/adapters/database/sql/pricing_repositories.py`

## 6. Billing and Operations

Billing:

- routes: `src/entrypoints/credits_routes.py`
- use case: `src/use_cases/billing`
- SQL repo: `src/adapters/database/sql/billing_repositories.py`

Operations:

- use case: `src/use_cases/operations`
- queue adapters: `src/adapters/queue.py`
- worker runtime: `src/services/workers/worker_runtime.py`
- active rate limiting: `src/services/rate_limit` with Redis and in-memory backends

## 7. LLM and Agent Layers

Provider runtime:

- `src/llm/provider_runtime.py`

Runtime-owned task contours:

- `src/runtime_agents/dialog_reply`

Product-agent contour:

- `src/adk_agents`

Canonical invocation contour:

- domain contracts: `src/domain/agent_runtime.py`
- use-case service and ports: `src/use_cases/agents`
- provider gateway: `src/adapters/agents/adk_agent_gateway.py`
- Product Card invocation adapter: `src/adapters/agents/product_card_generation.py`
- Garment Identity invocation adapter: `src/adapters/agents/garment_identity_analysis.py`
- approved artifact resolver: `src/adapters/agents/object_storage_artifact_resolver.py`
- SQL audit model/repository: `src/adapters/database/sql/agent_invocation_models.py`, `agent_invocation_repositories.py`
- migration: `alembic/versions/20260614_000011_agent_invocation_ledger.py`

Routes and workflows may use the invocation service, but must not import ADK agent roots directly.
Multimodal invocations pass only approved artifact references into the gateway. The resolver loads and integrity-checks transient bytes; the audit ledger never stores image payloads.
Provider-specific SDKs remain behind provider/runtime adapters. A future OpenAI, Anthropic, or local-model implementation must plug into the existing invocation/provider ports without changing product workflows.

Image-agent contract foundation:

- shared evidence, uncertainty, and safety models: `src/domain/image_agent_contracts.py`
- versioned image-agent requests, outputs, prompts, and deploy policies:
  - `human_identity_agent`
  - `garment_identity_agent`
  - `material_texture_agent`
  - `try_on_agent`
  - `quality_verifier_agent`
  - `repair_agent`
  - `fashion_stylist_agent`
- golden request fixtures: `tests/fixtures/agent_evaluations`

## 8. Compatibility Contours

The following modules still exist for compatibility and migration support:

- `src/adapters/database/firestore`

These are not the target foundation for new product workflows. New backend growth should continue through the portable SQL/object-storage/vector/runtime contour.

## 9. B2B Business Catalog

Last updated: `2026-06-29`

The B2B catalog is the seller-owned product data foundation for future Similar/Cheaper Search, marketplace connectors, Product Card reuse, and competitor analysis.

Core files:

- `src/domain/business_catalog.py` - merchant, product, offer, image, import job, import error models.
- `src/use_cases/business_catalog/service.py` - merchant/product/import/review orchestration.
- `src/use_cases/business_catalog/import_parser.py` - CSV parsing and row-level validation.
- `src/use_cases/business_catalog/search_projection.py` - approved-product projection for future search hydration.
- `src/use_cases/business_catalog/tenant_partitioning.py` - `standard`/`large` tenant routing policy and tier recommendation.
- `src/use_cases/business_catalog/tier_admin.py` - admin view model for merchant workload tier decisions.
- `src/use_cases/business_catalog/idempotency.py` - retry-safe mutation boundary.
- `src/use_cases/business_catalog/backpressure.py` - tier upload/import limits.
- `src/adapters/business_catalog/file_storage.py` - object-storage adapter for product media uploads.
- `src/adapters/business_catalog/in_memory_repository.py` - sandbox/test repository fallback.
- `src/adapters/database/sql/business_catalog_models.py` - SQL tables.
- `src/adapters/database/sql/business_catalog_repositories.py` - SQL repository.
- `src/entrypoints/business_catalog_routes.py` - business-facing API.
- `src/entrypoints/admin_business_catalog_routes.py` - admin review/tier API.

Business-facing routes:

- `GET /api/business/merchant`
- `POST /api/business/merchant`
- `GET /api/business/products`
- `POST /api/business/products`
- `POST /api/business/products/{product_id}/images`
- `POST /api/business/products/{product_id}/submit`
- `POST /api/business/catalog-imports`
- `GET /api/business/catalog-imports/{import_id}`
- `GET /api/business/catalog-imports/{import_id}/errors`

Admin routes:

- `GET /api/admin/business-catalog/products/pending`
- `POST /api/admin/business-catalog/products/{product_id}/approve`
- `POST /api/admin/business-catalog/products/{product_id}/reject`
- `GET /api/admin/business-catalog/merchants/tiers`
- `POST /api/admin/business-catalog/merchants/{merchant_id}/tier`

Reliability status:

- Admin approval is required before public search projection.
- `Idempotency-Key` is supported for CSV import, image upload, and submit-to-review.
- Backpressure returns `business_catalog_backpressure` before expensive processing starts.
- Infrastructure failures return structured operation errors and never silently succeed.
- Catalog CRUD does not depend on AI/model provider availability.
- Runtime wiring now exposes `business_catalog_service(settings)` through the standard dependency container.
- Staging smoke script: `scripts/business_catalog_staging_smoke.py`.
