# AI FitFabrica Portable Backend

This repository is the production backend for AI FitFabrica. It provides a deployable, vendor-neutral runtime contour for the web product, workers, storage, retrieval, and agent-driven workflows.

## Core Principles

*   **Deployable Day 0:** Fully functional and deployable from the start.
*   **Portable:** Cloud provider treated only as infrastructure host.
*   **Backend-First:** All business logic, computations, and security are encapsulated in the backend.
*   **Pluggable Adapters:** Easy to swap integrations (CRMs, messaging channels, LLM providers).
*   **Web-First:** Default runtime contour is the FitFabrica web/API path.
*   **Forward-Only Extension:** Designed for adding new product workflows without legacy ingress lock-in.

## Active Runtime Shape

`Web / Firebase Frontend -> Backend API -> Queue / Worker -> PostgreSQL / Redis / S3-compatible storage / Qdrant`

## Architectural Constraints

*   Backend orchestrates all side effects.
*   LLM is compute-only and returns strictly `reply_text` and `system_payload`.
*   Domain logic is strictly separated by layers: `entrypoints / use_cases / domain / adapters / runtime_agents / adk_agents`.
*   Agents do not orchestrate each other; the backend is the sole orchestrator.

## Portable Runtime Dependencies

*   PostgreSQL for canonical state and migrations.
*   Redis for distributed rate limiting and short-lived coordination.
*   S3-compatible object storage for binary artifacts.
*   Qdrant for vector bootstrap and namespace management.

## Stage 1 Foundation Surfaces

*   `src/adapters/database/sql`
*   `src/adapters/cache`
*   `src/adapters/storage`
*   `src/adapters/vector`
*   `src/services/runtime/portable_infrastructure.py`

## Stage 2 Identity Surfaces

*   `src/adapters/database/sql/identity_models.py`
*   `src/adapters/database/sql/identity_repositories.py`
*   `src/adapters/database/sql/identity_audit.py`
*   `src/entrypoints/runtime_dependencies.py`

## Stage 3 Object Storage Surfaces

*   `src/adapters/storage/contracts.py`
*   `src/adapters/storage/object_naming.py`
*   `src/adapters/storage/media_storage.py`
*   `src/adapters/storage/in_memory_object_storage.py`
*   `src/adapters/storage/s3_object_storage.py`
*   `src/entrypoints/try_on_routes.py`

## Current Try-On Storage Baseline

*   Try-On uploads now route through portable object storage.
*   Active runtime wiring uses `OBJECT_STORAGE_BACKEND=in_memory|s3`.
*   `try_on_job_repository_backend` may still use `firestore` as migration-state job persistence.
*   Public Try-On responses do not expose internal storage references such as bucket names or object keys.

## Stage 4 Vector Foundation Surfaces

*   `src/domain/vector_search.py`
*   `src/adapters/vector/namespaces.py`
*   `src/adapters/vector/qdrant_bootstrapper.py`
*   `src/adapters/vector/qdrant_filters.py`
*   `src/adapters/vector/qdrant_retriever.py`

## Current Vector Search Baseline

*   Qdrant is the active vector search layer.
*   PostgreSQL remains the source of truth; Qdrant stores embeddings plus filterable retrieval metadata.
*   The backend can now define namespaces, ensure collections exist, upsert points, and run typed similarity search.

## Stage 5 Provider Runtime Surfaces

*   `src/domain/provider_models.py`
*   `src/domain/provider_ports.py`
*   `src/llm/provider_runtime.py`
*   `src/adapters/ai/embedding_fake.py`
*   `src/adapters/ai/image_generation_stub.py`
*   `src/adapters/ai/image_editing_stub.py`
*   `src/entrypoints/runtime_dependencies.py`

## Current Provider Abstraction Baseline

*   The backend now owns a provider runtime that selects reasoning, agent runtime, embedding, and image adapters.
*   `LLMService` no longer constructs Gemini or Vertex providers directly.
*   Gemini structured reasoning and Vertex agent runtime remain the first implementations, but the business layer is now provider-blind.

## Stage 6 Try-On Rebase Surfaces

*   `src/adapters/database/sql/try_on_models.py`
*   `src/adapters/database/sql/try_on_repositories.py`
*   `src/adapters/database/sql/try_on_serialization.py`
*   `src/entrypoints/runtime_dependencies.py`
*   `src/entrypoints/try_on_routes.py`

## Current Try-On Rebase Baseline

*   Try-On uploads stay on the portable object storage path.
*   Try-On routes now resolve job storage and generation wiring through the composition root.
*   When portable SQL infrastructure is configured, Try-On job persistence prefers PostgreSQL.
*   `TRY_ON_GENERATION_BACKEND=sandbox_fake` remains the safe default.
*   `TRY_ON_GENERATION_BACKEND=provider_runtime` enables a provider-runtime-backed Try-On generation contour that still persists a deterministic placeholder artifact.
*   `TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on` enables the first real Vertex Virtual Try-On backend while keeping routes, workers, billing, and persistence unchanged.
*   All Try-On generation backends now pass through a dedicated backend quality-verifier step before the result is exposed.
*   Try-On now includes a backend repair step for locally fixable quality issues, followed by one more quality verification pass.
*   `TRY_ON_QUALITY_VERIFIER_BACKEND=model_backed` is now the active default and adds a structured reasoning decision layer on top of backend verification facts.
*   If the model-backed verifier is unavailable, the workflow falls back to deterministic verification and does not stall the Try-On job.
*   `TRY_ON_REPAIR_BACKEND=provider_runtime` is now the active default and uses the provider-runtime image-editing path for local Try-On correction, while deterministic repair remains the fallback.
*   `TRY_ON_STYLIST_BACKEND=model_backed` is now the active default and generates the final user-facing stylist explanation as a separate backend step after quality and repair.

## Stage 7 Similar Search Surfaces

*   `src/domain/similar_search.py`
*   `src/use_cases/similar_search`
*   `src/adapters/database/sql/catalog_models.py`
*   `src/adapters/database/sql/catalog_repositories.py`
*   `src/entrypoints/similar_search_routes.py`

## Current Similar Search Baseline

*   Similar search requests are handled fully on the backend.
*   Qdrant provides typed retrieval hits and filterable similarity search.
*   PostgreSQL stores product and marketplace truth used to hydrate and rank matches.
*   Cheaper-alternative decisions and explanations are owned by backend ranking code.
*   The API now exposes `/api/similar-search` as a structured route for retrieval and ranking.

## Stage 8 Product-Card Workflow Surfaces

*   `src/domain/product_card.py`
*   `src/use_cases/product_card`
*   `src/adapters/database/sql/product_card_models.py`
*   `src/adapters/database/sql/product_card_repositories.py`
*   `src/entrypoints/product_card_routes.py`

## Current Product-Card Baseline

*   Product-card jobs are now handled on the backend instead of living only as a workspace page.
*   PostgreSQL stores product-card jobs, source asset references, generated versions, and quality notes.
*   Portable object storage persists source product media before draft generation starts.
*   Fake product-card generation remains the safe default until a real provider-backed draft generator is approved.
*   The API now exposes `/api/product-cards` as a structured route for B2B product-card creation.

## Stage 8 Content-Package Workflow Surfaces

*   `src/domain/content_package.py`
*   `src/use_cases/content_package`
*   `src/adapters/database/sql/content_package_models.py`
*   `src/adapters/database/sql/content_package_repositories.py`
*   `src/entrypoints/content_package_routes.py`

## Current Content-Package Baseline

*   Content-package jobs are now handled on the backend instead of living only as a workspace page.
*   PostgreSQL stores content-package jobs, generated versions, and artifact references.
*   Portable object storage persists generated package artifacts and export-ready references.
*   Fake content-package generation remains the safe default until a real provider-backed asset generator is approved.
*   The API now exposes `/api/content-packages` as a structured route for B2B content-package creation.

## Stage 8 Pricing Workflow Surfaces

*   `src/domain/pricing.py`
*   `src/use_cases/pricing`
*   `src/adapters/database/sql/pricing_models.py`
*   `src/adapters/database/sql/pricing_repositories.py`
*   `src/entrypoints/pricing_routes.py`

## Current Pricing Baseline

*   Pricing jobs are now handled on the backend instead of living only as a presentation page.
*   PostgreSQL stores pricing jobs and persisted recommendation versions.
*   Catalog truth supplies the first comparable market evidence for pricing decisions.
*   Recommendation logic stays fully backend-owned and returns a structured result with market band and rationale.
*   The API now exposes `/api/pricing-jobs` as a structured route for B2B pricing recommendations.
 
## Project Documentation

*   `docs/plan.md` — Detailed implementation plan for this skeleton baseline.
*   `docs/bootstrap_checklist.md` — A checklist for bootstrapping a new client project from this skeleton.
*   `docs/env_setup_guide.md` — Guide for setting up environment variables and secrets.
*   `docs/deploy_guide.md` — Instructions for deploying the skeleton backend to Google Cloud.
*   `docs/day0_smoke_test_guide.md` — Guide for performing essential smoke tests on day 0.
*   `docs/core_optional_client_boundaries.md` — Defines what is considered core, optional, and client-specific.

## Local Setup (Python 3.11)

```bash
bash scripts/setup_test_env.sh
source .venv/bin/activate
cp .env.example .env
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## Validation

```bash
bash scripts/run_tests.sh
python scripts/check_architecture.py
python -m compileall src
```

## Portable Staging Contour

The repository now includes a vendor-neutral staging contour:

- `docker-compose.portable-staging.yml`
- `.env.portable-staging.example`
- `docs/runbooks/portable_staging_runtime.md`
- `.env.portable-remote-staging.example`
- `docs/runbooks/portable_remote_staging_vm.md`

This contour keeps PostgreSQL, Redis, S3-compatible object storage, and Qdrant under our control, while any cloud provider is treated only as a host platform.
For the standard web-first contour, set `MESSAGING_PROVIDER=none`. Telegram/PubSub ingress is removed from the active runtime baseline.

Use `python scripts/platform_foundation_smoke.py --env-file <portable-env> --require-ready` to validate a portable deployment pack before starting containers or provisioning a remote VM.
Use `sudo bash scripts/bootstrap_portable_host.sh` on a fresh Ubuntu/Debian VM and `bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local` for the first remote deploy pass.
Use `docs/runbooks/portable_remote_staging_ubuntu_22_04.md` as the exact first-pass bring-up path when you want one concrete deployment recipe instead of a generic runbook.
Use `docs/runbooks/firebase_hosting_to_gcp_vm_backend.md` when the frontend stays on Firebase Hosting and the portable backend runs on a GCP VM.

## FitFabrica Agent System

The repository now includes a dedicated FitFabrica product-agent contour under `src/adk_agents`:

- Wave 1: `human_identity_agent`, `garment_identity_agent`, `material_texture_agent`, `try_on_agent`, `quality_verifier_agent`, `repair_agent`, `fashion_stylist_agent`
- Wave 2: `orchestrator_agent`, `user_profile_agent`, `business_profile_agent`
- Wave 3: `marketplace_agent`, `trend_agent`, `pricing_agent`, `product_card_agent`, `cost_credits_agent`

These agents are exposed through `fitfabrica_agent_runtime_dependencies(...)` and return structured outputs only. Backend workflow code remains the only orchestrator for Try-On, pricing, search, billing, persistence, retry, and repair outcomes.

Reply-runtime status:

- `dialog_reply_task` is the canonical backend reply-task name.
- `src/runtime_agents/dialog_reply` is the canonical backend reply-runtime contour.
- dialog reply now uses only the canonical `src/runtime_agents/dialog_reply` contour and `dialog_reply_task`.
## Billing And Credits Core

The portable backend now includes a dedicated billing layer:

- durable credit accounts in PostgreSQL
- durable credit ledger events in PostgreSQL
- backend-owned workflow charging through `BillingService`
- free retry and free repair policy resolution in backend code
- balance and ledger API routes at `/api/credits/{owner_type}/{owner_id}` and `/api/credits/{owner_type}/{owner_id}/ledger`

Workflow integration is implemented for Try-On, product card, content package, and pricing. Active enforcement is gated by the runtime flag `billing_core_enabled` so the platform can adopt durable billing without breaking flows before accounts are seeded.

## Operations And Reliability Foundation

The portable backend now includes an initial operations contour:

- durable queue jobs in PostgreSQL
- durable worker leases in PostgreSQL
- portable queue backends for `in_memory` and `redis`
- backend-owned dispatch, lease, and worker runtime services
- health output that includes queue backend, queue depth, and worker identity
- smoke output that includes queue backend and worker name

This is the operations foundation, not the final public-workflow cutover. The queue and worker runtime exist and are test-covered, but public workflow routes are not yet fully moved onto dispatch-driven background execution.

Current cutover status:

- `product card`, `content package`, and `pricing` create routes now return accepted jobs and hand execution to the queue/worker contour
- health and smoke surfaces report operations runtime readiness
- `Try-On` create route now returns an accepted job and dispatches execution through the queue/worker contour for `complete` and `failed` sandbox modes
- `Try-On` `pending` sandbox mode remains an explicit non-dispatch test hook for polling clients
- `Try-On` can now switch independently between `sandbox_fake`, `provider_runtime`, and `vertex_virtual_try_on` generation backends without changing the route or persistence architecture
- `Try-On` now applies a backend-owned quality-verifier stage after generation and rejects results that fail deterministic verification before user exposure
- `Try-On` now attempts a backend repair pass when verification reports a locally fixable issue, then re-runs verification before exposing the result
