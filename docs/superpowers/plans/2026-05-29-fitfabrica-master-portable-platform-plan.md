# AI FitFabrica Master Portable Platform Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the project's Google-first foundation with a single portable enterprise platform and execute AI FitFabrica in a backend-first, scalable, provider-agnostic way.

**Architecture:** PostgreSQL becomes the source of truth, Qdrant becomes the vector layer, S3-compatible storage becomes the binary storage layer, Redis becomes the short-lived coordination layer, and the agent/model layer stays pluggable with Gemini plus Google ADK as the first provider implementation. Existing Firestore/GCS assumptions are treated as migration-state code, not as the target baseline.

**Tech Stack:** FastAPI, PostgreSQL, Qdrant, S3-compatible object storage, Redis, Gemini, Google ADK, Next.js, React, TypeScript.

---

## Scope Framing

This is the master plan for the whole project, not a single execution batch.

The project is too large to implement as one detailed task plan. Therefore this master plan defines:

- the only approved platform baseline
- the implementation order of major subsystems
- the dependency chain between stages
- which already-built work is reusable
- which detailed follow-up plans must be written next

Each stage below should later produce its own detailed implementation plan before code execution begins.

## Baseline Decision

- [x] **Step 1: Adopt one platform baseline**

Approved baseline:

- PostgreSQL
- Qdrant
- S3-compatible object storage
- Redis
- pluggable agent/model layer

Rejected baseline:

- Google-first persistence
- Firestore as primary truth
- GCS as primary storage contract
- multiple parallel platform variants

- [x] **Step 2: Record the approved architecture**

Architecture spec is written in:

- `docs/superpowers/specs/2026-05-29-fitfabrica-portable-platform-design.md`

This spec supersedes Google-first platform assumptions for future implementation work.

## Current Reusable Work

- [x] **Step 3: Identify work that remains valid**

The following existing work stays useful and should be preserved conceptually:

- backend-first layering and ports/adapters direction
- typed Try-On API contracts
- web application structure in `apps/web`
- agent separation and structured-output direction
- existing tests and route surfaces

- [x] **Step 4: Mark work that becomes migration-state**

The following existing work is no longer the target baseline:

- Firestore-backed identity runtime repositories
- Firestore-backed memory persistence as the long-term default
- GCS-backed Try-On storage as the long-term default
- Google-only platform assumptions in project docs

## Stage 1: Platform Foundation

**Outcome:** portable infrastructure contracts exist before broader feature expansion continues.

- [x] **Step 5: Write a dedicated platform foundation plan**

This next detailed plan must define:

- PostgreSQL integration baseline
- migration framework
- repository contracts for SQL persistence
- Redis integration baseline
- S3-compatible storage contract
- Qdrant client and collection contract

Expected output:

- one detailed plan for portable platform foundation
- detailed plan: `docs/superpowers/plans/2026-05-29-fitfabrica-platform-foundation-plan.md`

- [x] **Step 6: Implement platform foundation**

This stage should add:

- SQL adapter package and database session management
- migration setup
- S3 storage port and first adapter
- Redis runtime utilities
- Qdrant client and collection bootstrap abstractions

Stage exit criteria:

- app boots with portable infrastructure dependencies
- no production code requires Firestore or GCS to exist

## Stage 2: Identity Core Migration

**Outcome:** canonical identity and persona truth move into PostgreSQL.

- [x] **Step 7: Write a dedicated identity migration plan**

This plan must cover:

- `channel_identities`
- `identity_bindings`
- canonical `persons`
- lead and persona unification direction
- audit tables
- replacement of Firestore runtime identity repositories

Expected output:

- one detailed plan for identity core migration
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-identity-core-migration-plan.md`

- [x] **Step 8: Implement identity persistence in PostgreSQL**

This stage should produce:

- SQL tables and migrations
- repository implementations for identity core contracts
- runtime identity resolution backed by PostgreSQL
- migration-state compatibility boundaries where needed

Stage exit criteria:

- canonical identity resolution no longer depends on Firestore
- identity truth has transactional constraints and auditability

## Stage 3: Object Storage Migration

**Outcome:** binary artifacts move to a vendor-neutral storage contract.

- [x] **Step 9: Write a dedicated object storage plan**

This plan must cover:

- S3-compatible storage contract
- upload naming conventions
- tenancy and isolation rules
- signed URL policy
- lifecycle and cleanup rules

Expected output:

- one detailed plan for object storage migration
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-object-storage-migration-plan.md`

- [x] **Step 10: Implement S3-compatible media storage**

This stage should produce:

- storage adapter behind a neutral media port
- upload and retrieval flow for Try-On and future workflows
- migration path away from GCS-specific code

Stage exit criteria:

- uploads and generated artifacts no longer require GCS

## Stage 4: Vector Search Foundation

**Outcome:** vector retrieval is isolated from OLTP.

- [x] **Step 11: Write a dedicated vector foundation plan**

This plan must cover:

- Qdrant collection model
- embedding ownership and namespaces
- payload filtering rules
- replication and recovery assumptions
- reindexing strategy

Expected output:

- one detailed plan for vector foundation
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-vector-foundation-plan.md`

- [x] **Step 12: Implement Qdrant vector layer**

This stage should produce:

- vector adapter interfaces
- Qdrant client adapter
- collection bootstrap and health checks
- first retrieval APIs for products and garments

Stage exit criteria:

- vector search no longer depends on Google-managed search assumptions
- retrieval load is isolated from PostgreSQL

## Stage 5: Agent And Provider Abstraction Hardening

**Outcome:** the AI layer is explicitly replaceable without touching core business state.

- [x] **Step 13: Write a dedicated provider abstraction plan**

This plan must cover:

- model invocation ports
- embedding provider ports
- image generation and editing ports
- ADK/Gemini integration boundaries
- provider failover and fallback policy

Expected output:

- one detailed plan for provider abstraction hardening
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-provider-abstraction-plan.md`

- [x] **Step 14: Implement provider abstraction hardening**

This stage should produce:

- explicit provider-neutral contracts
- Gemini plus ADK adapter as the first implementation
- removal of provider assumptions from business logic

Stage exit criteria:

- the system can change AI provider without changing persistence architecture

## Stage 6: Try-On Workflow Rebase

**Outcome:** existing Try-On work is upgraded onto the portable baseline.

- [x] **Step 15: Write a dedicated Try-On rebase plan**

This plan must integrate and supersede the current Try-On implementation state:

- sandbox lifecycle routes and tests
- migration-state durable storage adapters
- existing frontend workflow and result handling

This new plan must state which pieces are reused and which are replaced.

- [x] **Step 16: Rebase Try-On onto PostgreSQL plus S3**

This stage should produce:

- SQL-backed job persistence
- S3-backed media storage
- retention and audit rules
- explicit Qdrant integration boundaries for related retrieval features

Stage exit criteria:

- Try-On no longer depends on Firestore or GCS as target architecture

## Stage 7: Similar Search And Marketplace Intelligence

**Outcome:** the product starts using the enterprise retrieval contour.

- [x] **Step 17: Write a dedicated similar search plan**

This plan must cover:

- garment and product embedding flow
- retrieval and ranking
- marketplace data normalization
- cheaper alternative logic

Expected output:

- one detailed plan for similar search foundation
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-similar-search-foundation-plan.md`

- [x] **Step 18: Implement similar search foundation**

This stage should produce:

- vector retrieval endpoints
- structured ranking results
- backend-owned comparison logic

Stage exit criteria:

- similar search is backend-owned and uses Qdrant plus PostgreSQL

## Stage 8: Product Card, Content Package, And B2B Flows

**Outcome:** B2B workflows move from UI-only readiness to backend-owned execution.

- [x] **Step 19: Write dedicated plans for each B2B workflow**

Required follow-up plans:

- product card workflow
- content package workflow
- pricing workflow

Detailed plans written:

- `docs/superpowers/plans/2026-05-31-fitfabrica-product-card-workflow-plan.md`
- `docs/superpowers/plans/2026-05-31-fitfabrica-content-package-workflow-plan.md`
- `docs/superpowers/plans/2026-05-31-fitfabrica-pricing-workflow-plan.md`

- [x] **Step 20: Implement B2B workflow backend contours**

This stage should produce:

- job creation
- persistence
- output versioning
- storage references
- audit and quality control

Stage exit criteria:

- B2B flows are no longer presentation-only routes

Completed backend contours:

- product card workflow foundation
- content package workflow foundation
- pricing workflow foundation

## Stage 9: Credits, Billing, And Economics

**Outcome:** commercial logic moves into backend-owned durable records.

- [x] **Step 21: Write a dedicated credits and billing plan**

This plan must cover:

- credit ledger
- workflow cost model
- free repair and retry policy
- refunds and adjustments
- reporting boundaries

Expected output:

- one detailed plan for billing and credits core
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-credits-and-billing-plan.md`

- [x] **Step 22: Implement billing and credits core**

Stage exit criteria:

- credits are calculated only on the backend
- durable ledger exists in PostgreSQL

Completed billing contours:

- `credit_accounts` SQL foundation
- `credit_ledger_events` SQL foundation
- backend-owned `BillingService` and pricing-policy resolver
- credits balance and ledger API routes
- workflow integration boundaries for Try-On, product card, content package, and pricing
- guarded activation path so billing enforcement can be enabled without breaking unseeded accounts

## Stage 10: Reliability, Scale, And Operations

**Outcome:** the system is ready for sustained production load.

- [x] **Step 23: Write a dedicated reliability and operations plan**

This plan must cover:

- worker topology
- queue and background execution
- PostgreSQL backup and replica strategy
- Qdrant redundancy strategy
- storage durability and export handling
- observability and alerting
- rate limiting and abuse controls

Expected output:

- one detailed plan for reliability and operations
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-reliability-operations-plan.md`

- [x] **Step 24: Implement production reliability controls**

Stage exit criteria:

- the system has explicit operational contours for sustained load
- heavy jobs are isolated from request-response paths

Completed reliability contours:

- durable queue jobs and worker leases in PostgreSQL
- portable queue backends for `in_memory` and `redis`
- backend-owned dispatch, lease, and worker runtime services
- health output includes queue backend, queue depth, and worker identity
- smoke output includes queue backend and worker identity
- B2B create routes now enqueue accepted jobs and complete execution on the worker path
- Try-On create route now enqueues accepted jobs and completes `complete` and `failed` sandbox execution on the worker path
- Try-On `pending` sandbox mode remains an explicit non-dispatch polling hook for frontend and API verification

## Stage 11: FitFabrica Agent System

**Outcome:** project-specific product agents are defined and implemented as a dedicated backend-owned ADK contour instead of staying implicit inside generic provider/runtime plumbing.

- [x] **Step 34: Write a dedicated FitFabrica agent system plan**

This plan must cover:

- target `src/adk_agents` structure for FitFabrica
- which current legacy agents are retained as infrastructure-only support agents
- which legacy agents are removed or archived
- product-agent contracts for:
  - orchestrator
  - user profile
  - business profile
  - human identity
  - garment identity
  - material and texture
  - try-on
  - product card
  - fashion stylist
  - marketplace
  - trend
  - pricing
  - quality verifier
  - repair
  - cost and credits
- execution order by business priority so B2C Try-On agents land before lower-priority expansions
- backend orchestration boundaries so agents stay structured-output only and do not own workflow control

Expected output:

- one detailed plan for the FitFabrica agent system
- detailed plan: `docs/superpowers/plans/2026-06-02-fitfabrica-agent-system-plan.md`

- [x] **Step 35: Implement FitFabrica agent system in `src/adk_agents`**

This stage should produce:

- cleanup of temporary and legacy agent folders that do not belong to FitFabrica target architecture
- dedicated FitFabrica ADK agent packages under `src/adk_agents`
- explicit contracts, prompts, and deploy configs per approved agent role
- integration boundaries that keep orchestration in backend workflow code, not inside agents

Current implementation status:

- Wave 1 implemented:
  - `human_identity_agent`
  - `garment_identity_agent`
  - `material_texture_agent`
  - `try_on_agent`
  - `quality_verifier_agent`
  - `repair_agent`
  - `fashion_stylist_agent`
- Wave 2 implemented:
  - `orchestrator_agent`
  - `user_profile_agent`
  - `business_profile_agent`
- Wave 3 implemented:
  - `marketplace_agent`
  - `trend_agent`
  - `pricing_agent`
  - `product_card_agent`
  - `cost_credits_agent`
- `fitfabrica_agent_runtime_dependencies(...)` now exposes the approved product-agent runtime bundle.
- `daily_memory_agent_tmp20260425_024853` has been removed from the active runtime surface.
- `src/adk_agents/primary_agent` has been removed from the active ADK surface.
- `dialog_reply_task` is now the canonical backend reply-task name.
- `src/runtime_agents/dialog_reply` is now the canonical backend reply-runtime contour.
- the remaining reply-runtime compatibility contour has been removed; only the canonical dialog-reply runtime remains in the active FitFabrica baseline.
- Stage 11 is now considered complete because the remaining legacy reply-task surface is compatibility-only and no longer defines active architecture.

Stage exit criteria:

- `src/adk_agents` reflects FitFabrica agent roles rather than legacy generic agents
- required memory agents remain only as infrastructure support where still needed
- product agents exist only for the stages that are actually ready to use them in backend workflows

Post-Stage-11 next step:

- choose the first portable deployment target for the backend runtime contour
- execute portable staging rollout on the selected host
- wire Firebase-hosted frontend surfaces to the portable backend API and health/status contours

## Documentation Alignment Work

- [x] **Step 25: Rewrite architecture docs to match the new baseline**

Completed alignment:

- `AGENTS.md` project instructions now describe the portable baseline
- `docs/project_description.md` reflects the active platform decision
- `docs/project_structure.md` marks Google-specific areas as migration-state
- legacy Try-On architecture docs that enforced GCS/Firestore as the target were removed

- [x] **Step 26: Mark superseded plans and migration-state documents**

Completed cleanup:

- superseded implementation reports and obsolete Try-On planning docs were removed
- active architecture now lives in the portable platform spec and this master plan
- migration-state code is described as temporary in the remaining docs

## Immediate Next Planning Sequence

- [x] **Step 27: First detailed follow-up plan**

Completed:

- portable platform foundation plan

- [x] **Step 28: Second detailed follow-up plan**

Completed:

- identity core migration plan

- [x] **Step 29: Third detailed follow-up plan**

Completed:

- object storage migration plan

- [x] **Step 31: Fourth detailed follow-up plan**

Completed:

- vector foundation plan

- [x] **Step 32: Fifth detailed follow-up plan**

Completed:

- provider abstraction plan

- [x] **Step 33: Sixth detailed follow-up plan**

Completed:

- Try-On rebase plan

## Execution Rule

- [ ] **Step 30: Do not continue feature expansion on the old baseline**

From this point, new implementation work should not deepen the Google-first persistence architecture. New feature work must either:

- land on the portable baseline directly
- or be explicitly marked as temporary migration-state work
