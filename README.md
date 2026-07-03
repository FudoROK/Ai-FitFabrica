# AI FitFabrica

AI FitFabrica is a backend-first fashion commerce platform. The browser is a thin client, while all workflow orchestration, billing, persistence, quality gates, and agent/runtime integration stay on the backend.

## Current Shape

```text
apps/web (Next.js, TypeScript)
  -> FastAPI API
  -> workflow runtime / queue / workers
  -> PostgreSQL / Redis / S3-compatible object storage / Qdrant
  -> provider runtime / product agents
```

## Repository Areas

- `apps/web` - production web frontend on Next.js App Router.
- `src/entrypoints` - FastAPI routes and runtime wiring.
- `src/use_cases` - application workflows.
- `src/domain` - typed business models and contracts.
- `src/adapters` - SQL, storage, vector, queue, AI, and external integrations.
- `src/runtime_agents` - runtime-owned dialog and memory tasks.
- `src/adk_agents` - FitFabrica product-agent catalog.
- `tests` - backend and frontend contract/regression coverage.
- `docs` - project documentation and runbooks.

## Active Web Routes

Public:

- `/`
- `/for-you`
- `/business`
- `/capabilities`
- `/pricing`
- `/how-it-works`
- `/contacts`
- `/privacy`
- `/sign-in`

Workspace:

- `/workspace`
- `/workspace/new-fitting`
- `/workspace/try-on`
- `/workspace/try-on/new`
- `/workspace/try-on/result`
- `/workspace/similar`
- `/workspace/similar-search`
- `/workspace/product-card`
- `/workspace/content-package`
- `/workspace/outfit-builder`
- `/workspace/history`
- `/workspace/credits`
- `/workspace/business-profile`
- `/workspace/integrations`
- `/workspace/projects`
- `/workspace/settings`
- `/workspace/style-profile`
- `/workspace/chat`

## Active API Routes

- `GET /health`
- `GET /ready`
- `GET /time`
- `GET /api/workspace/bootstrap`
- `GET /api/workspace/capabilities`
- `POST /api/workspace/capabilities/{capability}/assert`
- `POST /api/workspace/actions/marketplace-publish`
- `POST /api/workspace/actions/catalog-import`
- `POST /api/workspace/actions/catalog-sync`
- `GET /api/workspace/business-profile`
- `POST /api/workspace/business-profile`
- `GET /api/workspace/integrations`
- `POST /api/workspace/integrations`
- `GET /api/workspace/outfit-builder/brief`
- `GET /api/workspace/outfit-builder/requests`
- `GET /api/workspace/outfit-builder/requests/{request_id}`
- `POST /api/workspace/outfit-builder/requests`
- `GET /api/credits/{owner_type}/{owner_id}`
- `GET /api/credits/{owner_type}/{owner_id}/ledger`
- `POST /api/try-on/jobs`
- `GET /api/jobs/{job_id}/status`
- `GET /api/jobs/{job_id}/result`
- `POST /api/similar-search`
- `POST /api/product-cards`
- `GET /api/product-cards/{job_id}`
- `GET /api/product-cards/{job_id}/result`
- `POST /api/content-packages`
- `GET /api/content-packages/{job_id}`
- `GET /api/content-packages/{job_id}/result`
- `POST /api/pricing-jobs`
- `GET /api/pricing-jobs/{job_id}`
- `GET /api/pricing-jobs/{job_id}/result`

## Runtime Wiring

The composition root is split into focused modules:

- `src/entrypoints/runtime_dependencies.py` - stable public entrypoint for runtime access.
- `src/entrypoints/runtime_dependency_contracts.py` - cache keys and runtime dataclasses.
- `src/entrypoints/runtime_dependency_builders.py` - workflow and infrastructure builders.

This keeps startup lighter and makes wiring testable without pulling heavy ADK or Vertex imports into the startup path.

Product workflows invoke agents only through the canonical backend-owned `AgentInvocationService`. The service enforces timeout and strict output validation, maps provider failures into typed results, and writes a safe PostgreSQL audit record without raw prompts, secrets, payloads, or image bytes.

## Compatibility Contours

- PostgreSQL, Redis, S3-compatible object storage, Qdrant, backend queues, and provider-neutral runtime wiring are the active portable baseline.
- Older Firestore and memory-layer support contours still exist only in isolated non-primary areas.
- Legacy Try-On Firestore/GCS storage adapters and the old identity Firestore runtime fallback have been removed.
- The old Firestore-specific rate limiter has also been removed; the active rate-limit surface is Redis or in-memory only.
- The old internal `/tasks/memory-summary` route and its dedicated runtime container have also been removed from the active HTTP surface.
- New product workflows should extend the portable backend contour, not re-expand Firestore-first runtime paths.

## Local Backend Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## Local Frontend Setup

```powershell
Set-Location apps/web
npm install
npm run dev
```

## Verification

Verified on `2026-06-14`:

- `.venv\Scripts\python.exe scripts\check_architecture.py`
- `.venv\Scripts\python.exe -m compileall src`
- `.venv\Scripts\python.exe -m pytest --collect-only -q`
- `.venv\Scripts\python.exe -m pytest -q -x --maxfail=1`
- `npm run lint` in `apps/web`
- `npm run typecheck` in `apps/web`
- `npm run build` in `apps/web`

At the time of verification the active backend/frontend checks were green, including full backend pytest, architecture checks, and frontend lint/typecheck/build.

## Documentation

- [System Documentation](/C:/Code/Ai%20Fitfabrica/docs/current_system_full_documentation.md)
- [Backend File Catalog](/C:/Code/Ai%20Fitfabrica/docs/backend_file_catalog.md)
- [Frontend File Catalog](/C:/Code/Ai%20Fitfabrica/docs/frontend_file_catalog.md)
- `docs/runbooks` - deployment and operations runbooks

## Current Standard

- No business logic in React components.
- No direct model/provider calls from the browser.
- No decorative routes or placeholder CTA links in active UI flows.
- Typed contracts at API boundaries.
- Backend-owned billing, retry, repair, and quality verification.
- No Python files under `src/` remain above the 300-line decomposition target.
