# AI FitFabrica Tests Description

## Purpose

This document describes the current testing strategy without duplicating a line-by-line catalog of every test file.

The repository test suite is intended to protect:

- backend domain and use-case behavior
- provider and transport contracts
- architecture boundaries
- security and idempotency contours
- Try-On workflow behavior
- frontend and backend contract alignment

## Main Test Groups

### Backend Behavior Tests

These tests validate:

- domain rules
- use cases
- route behavior
- typed error envelopes
- runtime orchestration behavior

Primary coverage areas include:

- dialog and inbound handling
- identity resolution
- LLM/provider contracts
- memory layer
- Try-On workflow

### Architecture Guardrail Tests

The `tests/architecture` suite enforces structural rules such as:

- layer boundaries
- runtime-agent restrictions
- Firestore contour guardrails during migration-state operation
- transport neutrality

These tests are especially important while the project is being migrated from the old baseline to the new portable baseline.

### Try-On Tests

The Try-On suite covers:

- sandbox lifecycle
- storage selection and wiring
- storage error handling
- frontend route alignment
- async result polling behavior

These tests currently prove that the workflow works, but they do not mean Firestore or GCS are the approved long-term target architecture.

### Frontend Verification

Frontend quality is validated through:

- `npm run lint`
- `npm run typecheck`
- `npm run build`

These checks ensure the current Next.js application remains consistent and production-buildable.

## Current Verification Baseline

Use this command set for repository verification:

```bash
pytest -q
cd apps/web && npm run lint
cd apps/web && npm run typecheck
cd apps/web && npm run build
```

## Documentation Rule

This file is intentionally concise. The source of truth for exact test coverage is the `tests/` directory itself, not a manually maintained giant file inventory.
