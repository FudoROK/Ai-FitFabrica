# AI FitFabrica: Current System Documentation

Last updated: `2026-06-14`

## 1. System Purpose

AI FitFabrica is a backend-first fashion-commerce platform.

The active product rule is simple:

- the frontend sends typed requests and renders state;
- the backend owns workflows, persistence, billing, retry, repair, and quality gates;
- provider runtime and product agents are invoked only from backend contours.

## 2. Active Runtime Contour

```text
Next.js frontend
  -> FastAPI API
  -> use cases / runtime wiring
  -> queue + worker
  -> PostgreSQL / Redis / S3-compatible object storage / Qdrant
  -> provider runtime + FitFabrica product agents
```

## 3. Frontend Baseline

Active frontend lives in `apps/web`.

Stack:

- Next.js App Router
- React
- TypeScript
- Tailwind CSS

Public routes:

- `/`
- `/for-you`
- `/business`
- `/capabilities`
- `/pricing`
- `/how-it-works`
- `/contacts`
- `/privacy`
- `/sign-in`

Workspace routes:

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

Workspace shell is now aligned to a thin-client model:

- backend bootstrap drives page state;
- loading, error, empty, success, and disabled states are explicit;
- guarded actions use capability verdicts from the backend;
- React components do not own workflow or billing logic.

## 4. Backend Baseline

Active backend lives in `src`.

Main layers:

- `src/entrypoints` - FastAPI routes and runtime composition root
- `src/use_cases` - application workflows
- `src/domain` - typed business models and contracts
- `src/adapters` - SQL, queue, object storage, vector, AI, and integration adapters
- `src/runtime_agents` - runtime-owned dialog and memory tasks
- `src/adk_agents` - approved FitFabrica product-agent roots

Main entrypoints:

- `src/main.py` - API bootstrap
- `src/worker.py` - worker bootstrap
- `src/entrypoints/http_routes.py` - HTTP route aggregator

## 5. Runtime Wiring

The composition root is no longer one large startup file.

Current structure:

- `src/entrypoints/runtime_dependencies.py` - stable public runtime entrypoint
- `src/entrypoints/runtime_dependency_contracts.py` - cache keys and runtime bundles
- `src/entrypoints/runtime_dependency_builders.py` - runtime bundle builders
- `src/entrypoints/runtime_dependency_foundation_builders.py`
- `src/entrypoints/runtime_dependency_workflow_builders.py`
- `src/entrypoints/runtime_dependency_product_card_builder.py`
- `src/entrypoints/runtime_dependency_operations_builders.py`

This keeps the startup path lighter and avoids eager ADK or Vertex imports during simple runtime wiring import.

Additional current-state notes:

- the FitFabrica product-agent runtime bundle is now strongly typed against `BaseAgent` roots instead of `Any`;
- product workflows must invoke agents through the canonical `AgentInvocationService` and `AgentInvocationPort`;
- every canonical invocation validates the structured output and persists safe audit metadata in PostgreSQL;
- the audit ledger stores versions, provider/model, latency, confidence, cost metadata, field names, and safe errors, but never raw prompts, unrestricted payloads, secrets, or image bytes;
- legacy internal memory-summary task ingress is no longer part of the active HTTP surface.

## 6. Active API Surface

Service:

- `GET /health`
- `GET /time`

Workspace:

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

Billing:

- `GET /api/credits/{owner_type}/{owner_id}`
- `GET /api/credits/{owner_type}/{owner_id}/ledger`

Workflow routes:

- `POST /api/try-on/jobs`
- `GET /api/jobs/{job_id}/status`
- `GET /api/jobs/{job_id}/result`
- `POST /api/similar-search`
- `POST /api/product-cards`
- `GET /api/product-cards/{job_id}`
- `GET /api/product-cards/{job_id}/result`
- `GET /api/product-cards/{job_id}/garment-analysis`
- `POST /api/content-packages`
- `GET /api/content-packages/{job_id}`
- `GET /api/content-packages/{job_id}/result`
- `POST /api/pricing-jobs`
- `GET /api/pricing-jobs/{job_id}`
- `GET /api/pricing-jobs/{job_id}/result`

## 7. Workflow Baseline

Try-On:

- uploads go through backend validation;
- Human Identity, Garment Identity, and Material / Texture agents are mandatory backend-controlled parallel gates before generation outside isolated test runtimes;
- validated human-preservation analysis and the backend continuation verdict are persisted with the Try-On job;
- Human Identity policy requires a single fully visible human subject, sufficient Try-On body coverage, low/medium-safe occlusion risk, and explicit required-region coverage before normal Try-On can proceed;
- validated garment and visible-material snapshots are persisted as separate Try-On child entities;
- failed, invalid, unsuitable, low-confidence, or high-uncertainty required analysis blocks generation and charges zero credits;
- the Try-On Instruction Agent receives only the three approved structured snapshots, never source artifacts or storage references;
- its validated typed instruction is persisted as a separate child entity and is mandatory input for every generation adapter;
- failed, low-confidence, or high-uncertainty instruction generation blocks image generation and charges zero credits;
- generation executes only through `TryOnGenerationPort`; provider/runtime failures are converted into a persisted `generation_failed` job with zero charged credits;
- real staging verification on `2026-06-15` confirmed four sequential `succeeded/passed` ledger rows for the three parallel analyses and the Try-On Instruction Agent, plus a persisted instruction child row;
- real staging verification on `2026-06-15` confirmed three parallel `succeeded/passed` invocation ledger rows and persisted garment/material child entities for one Try-On trace;
- the same staging job was rejected later by the existing Quality Verifier because sandbox-placeholder generation is not a production-quality image; analysis-bundle execution itself passed;
- media storage goes through object-storage abstraction;
- job persistence prefers SQL when portable infrastructure is configured;
- legacy GCS and Firestore Try-On storage adapters are removed from the active tree;
- quality verification and repair stay on the backend;
- billing is backend-owned and runtime-gated.

Similar Search:

- retrieval and ranking are backend-owned;
- Qdrant is the active vector layer;
- catalog truth comes from backend repositories.

Product Card / Content Package / Pricing:

- each workflow has its own route module, use case, and runtime bundle;
- background execution goes through operations runtime;
- billing remains backend-owned;
- persistence prefers SQL repositories.
- Garment Identity is a mandatory fail-closed stage before Product Card generation outside the isolated test environment;
- Garment Identity is the only Product Card stage that reads the source image through an integrity-checked portable object-storage artifact reference;
- validated Garment Identity analysis is persisted once per Product Card job and exposed through `GET /api/product-cards/{job_id}/garment-analysis`;
- Product Card generation receives only the persisted structured Garment Identity analysis and does not re-read or re-analyze the source image;
- outside the isolated test environment, Product Card generation invokes its versioned agent contract through the canonical `AgentInvocationService`;
- deterministic Garment Identity and Product Card adapters are test-only; provider, contract, low-confidence, or high-uncertainty failures mark the job as failed and do not charge completion credits;
- `/workspace/product-card` creates real Product Card jobs through `POST /api/product-cards`, polls the job endpoint, and reads the persisted result endpoint;
- Product Card input includes a persisted category, target channel, brand tone, title, and validated product image;
- Product Card creation is guarded by the backend capability service and the unified person-credit account shown by workspace bootstrap;
- workspace bootstrap exposes the backend-owned Product Card credit cost;
- publish, catalog import, and catalog sync remain visibly locked in web until real production pipelines are connected.
- sidebar, dashboard, and credits use one capability-aware CTA component; denied actions render as disabled buttons without navigable links.

## 8. Providers and Agents

Provider runtime lives in `src/llm/provider_runtime.py`.

FitFabrica product-agent contour lives in `src/adk_agents` and is loaded only through lazy runtime wiring.

Important constraints:

- no eager ADK or Vertex import in the normal startup path;
- workflows and routes do not import ADK agent roots directly;
- workflows depend on provider-neutral ports and the canonical invocation service, never on Gemini, Vertex, OpenAI, Anthropic, or local-model SDKs;
- adding OpenAI, Anthropic, or a local model requires a new provider adapter and runtime configuration only; Product Card workflow, API contracts, persistence, and billing do not change;
- current implemented provider runtimes are Gemini/Vertex-oriented plus deterministic test fakes; OpenAI, Anthropic, and local provider adapters are not implemented yet;
- agents do not import each other or the backend invocation gateway;
- provider failures, timeouts, and contract-validation failures return typed backend envelopes;
- the seven image-workflow agents expose strict request and output contracts;
- image-agent prompts and deploy configs bind explicit prompt and contract versions;
- Quality Verifier, Repair, and Material contracts enforce semantic invariants before workflow use;
- semantic agent failures are rejected; only transport formatting may be repaired by future runtime policy;
- production Try-On invokes Human Identity only through the canonical AgentInvocationService; tests use an explicit deterministic adapter and never call external providers;
- Human Identity sends an approved artifact reference through the canonical gateway; the backend resolves and integrity-checks the object, then passes transient image bytes to the multimodal Gemini runtime;
- text-only agent runtimes fail closed when an invocation requires artifacts; image bytes and temporary access details are never persisted in the invocation ledger;
- staging uses the direct `GeminiStructuredProvider` with `gemini-2.5-flash` through Google Gen AI SDK; real text and multimodal smoke calls return validated structured JSON;
- deprecated Vertex AI generative modules are forbidden by architecture guardrail; Google SDK calls remain isolated inside the provider adapter contour;
- the real staging Product Card chain was verified on `2026-06-15`: Garment Identity and Product Card both succeeded through `gemini-2.5-flash`, shared one trace ID, and persisted the reusable garment analysis;
- the legacy global `VERTEX_AGENT_RESOURCE` requirement was removed because the canonical direct Gemini runtime does not use a Reasoning Engine resource;
- frontend does not call model providers directly;
- orchestration remains backend-owned.

## 9. Data Foundation

Active portable foundation:

- PostgreSQL - canonical durable state
- Redis - queue, coordination, and rate limiting
- S3-compatible object storage - media and artifacts
- Qdrant - vector search

Compatibility contours still present:

- `src/adapters/database/firestore`

The Firestore contour is retained only in older support areas. New production workflows should extend the portable backend contour instead of expanding Firestore-first paths.

## 10. Verification Baseline

Verified on `2026-06-14`:

- `scripts/check_architecture.py`
- `python -m compileall src`
- `pytest --collect-only -q`
- `pytest -q -x --maxfail=1`
- `npm run lint` in `apps/web`
- `npm run typecheck` in `apps/web`
- `npm run build` in `apps/web`

Latest full backend result on `2026-06-15`: `629 passed`. Real Human Identity visual-accuracy validation still requires an approved staging test image and evaluation fixture.

## 11. Current Cleanliness Baseline

- active frontend routes are real and wired through backend state;
- runtime wiring is decomposed and lazily loaded;
- no Python files under `src/` remain above the 300-line decomposition target;
- temporary local artifacts are excluded from the active repository contour;
- compatibility paths are isolated instead of acting as the primary architecture.
