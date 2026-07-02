# AI FitFabrica Project Description

## Purpose

AI FitFabrica is a backend-first fashion-commerce platform built around agent workflows.

The product is split into two major contours:

- B2C: virtual try-on, outfit recommendations, similar and cheaper product discovery
- B2B: product-card generation, marketplace content packages, pricing support

The core product rule is stable:

`UI -> backend workflow -> agents/tools -> persistence -> result`

The frontend is only a thin client. It does not own orchestration, billing, retry, repair, or agent decisions.

## Active Architecture Baseline

The repository is currently moving on a portable enterprise baseline:

- FastAPI backend
- PostgreSQL as primary structured persistence
- Redis for cache, coordination, and idempotency
- S3-compatible object storage for media and artifacts
- Qdrant for vector retrieval
- provider-neutral runtime ports for reasoning, embeddings, and image operations

The backend remains the only orchestration authority.

## Main Product Workflows

The active backend surface is organized around these business workflows:

- Try-On
- Similar Search
- Product Card
- Content Package
- Pricing
- Credits and billing

Each workflow is expected to follow the same platform rules:

- typed contracts
- backend-owned persistence
- explicit status handling
- structured errors
- testable use-case boundaries

## Agents

Agents are backend-controlled roles with structured outputs.

They may analyze, classify, generate, verify, or recommend, but they do not:

- write business state directly
- orchestrate each other freely
- decide billing
- bypass backend validation

The active product-agent baseline is documented in:

- `README.md`
- `docs/current_system_full_documentation.md`
- `docs/refactor_status_2026-06-13.md`

## Documentation Rule

This file is a short orientation document.

For current architecture truth, use:

- `README.md`
- `docs/current_system_full_documentation.md`
- `docs/backend_file_catalog.md`
- `docs/frontend_file_catalog.md`

Historical planning artifacts under `docs/superpowers/` are reference material only and must not be treated as the current implementation contract.
