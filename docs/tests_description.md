# AI FitFabrica Tests Description

## Purpose

This document describes the current testing strategy without duplicating a line-by-line catalog of every test file.

The repository test suite is intended to protect:

- backend domain and use-case behavior
- provider and transport contracts
- canonical agent invocation validation, timeout, failure mapping, and safe audit persistence
- approved agent-artifact resolution, integrity validation, multimodal provider delivery, and text-only runtime fail-closed behavior
- image-agent request/output contracts, prompt policy, semantic invariants, and golden evaluation fixtures
- architecture boundaries
- security and idempotency contours
- Try-On workflow behavior
- Product Card mandatory Garment Identity analysis and fail-closed workflow behavior
- workflow cost map, provider price config, credits pricing, and offline cost reporting
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
- Try-On workflow

### Architecture Guardrail Tests

The `tests/architecture` suite enforces structural rules such as:

- layer boundaries
- runtime-agent restrictions
- support-only Firestore contour guardrails where those boundaries still exist
- transport neutrality
- no direct ADK agent-root imports from routes or use cases
- no direct cross-agent or agent-to-gateway imports
- no `Any` in active image-agent packages

These tests are especially important because the repository still protects a few isolated support contours while the active product baseline follows the portable backend architecture.

### Try-On Tests

The Try-On suite covers:

- sandbox lifecycle
- mandatory parallel Human Identity, Garment Identity, and Material / Texture analysis before generation
- backend continuation policy and fail-closed behavior
- hardened Human Identity suitability policy for headshot crops, face occlusion, multiple subjects, missing required body regions, and insufficient body coverage
- required-analysis SQL round-trip and migration chain
- Try-On Instruction Agent structured-only input boundary, fail-closed policy, workflow wiring, SQL round-trip, and migration chain
- generation-port execution, Vertex/provider adapter wiring, and fail-closed generation failure handling
- Human Identity artifact-reference mapping without raw image persistence
- storage selection and wiring
- storage error handling
- frontend route alignment
- async result polling behavior

The active Try-On storage tests protect the portable SQL and object-storage contour. Removed Firestore and GCS Try-On adapters are not part of the current production baseline.

### Product Card Tests

The Product Card suite covers:

- mandatory Garment Identity analysis before generation
- analysis contract mapping, confidence policy, and fail-closed behavior
- one persisted reusable analysis per Product Card job
- Product Card generation from structured analysis without source-image access
- SQL round-trip, migration chain, runtime wiring, routes, billing, and architecture boundaries

### Frontend Verification

Frontend quality is validated through:

- `npm run lint`
- `npm run typecheck`
- `npm run build`

These checks ensure the current Next.js application remains consistent and production-buildable.

## Current Verification Baseline

Use this command set for repository verification:

```powershell
.venv\Scripts\python.exe scripts\no_billing_acceptance_gate.py
.venv\Scripts\python.exe scripts\no_billing_acceptance_gate.py --full-backend --skip-frontend-build
.venv\Scripts\python.exe scripts\web_dependency_audit.py --require-ready
```

Latest full backend result on `2026-07-08`: `1202 passed`, `1 warning`.

Current frontend verification is included in `scripts/no_billing_acceptance_gate.py`:

- `npm run typecheck`
- `npm run lint`
- `npm run build`

Current web dependency evidence is included in `scripts/web_dependency_audit.py --require-ready`. The gate blocks high/critical npm findings and records low/moderate findings as evidence.

Latest Human Identity hardening result on `2026-06-16`: targeted Human Identity policy, adapter, and workflow checks passed with `37 passed`; architecture guardrails passed; staging API/worker images were rebuilt and policy matrix verification is documented in `docs/reports/2026-06-16-human-identity-policy-hardening-report.md`.

Latest Workflow Agent Cost Map result on `2026-06-16`: provider price config, workflow cost estimator, credits pricing policy, cost-map document contract, CLI report, and agent invocation cost metadata checks passed with `22 passed`.

## Documentation Rule

This file is intentionally concise. The source of truth for exact test coverage is the `tests/` directory itself, not a manually maintained giant file inventory.
