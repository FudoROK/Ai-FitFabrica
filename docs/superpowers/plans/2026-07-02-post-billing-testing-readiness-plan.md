# Post-Billing Testing Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare AI FitFabrica for calm end-to-end testing immediately after Google/Gemini/Vertex billing and provider access are restored.

**Architecture:** Keep the existing backend-first architecture: frontend submits DTOs/uploads only, FastAPI owns workflow execution, agents return structured JSON, backend owns billing/credits, quality gates, repair/retry decisions, and persistence. This plan does not add hidden scraping, frontend AI calls, or A2A agent contracts.

**Tech Stack:** FastAPI, PostgreSQL, Redis worker, S3-compatible object storage/MinIO, Qdrant, Gemini/Google Gen AI, Vertex Virtual Try-On, Next.js, TypeScript, Firebase Hosting, staging VM.

---

## Current Truth From Documents

Canonical sources reviewed:

- `docs/00_PROJECT_MASTER_PLAN.md`
- `docs/01_ACTION_LOG_CHECKLIST.md`
- `docs/02_TECHNICAL_PROJECT_MAP.md`
- `docs/03_AGENT_SYSTEM_GUIDE.md`
- `docs/04_OWNER_REMAINING_WORK.md`
- `docs/costs/credits_policy_v1.md`
- `docs/costs/credits_pricing_table_v1.md`
- `docs/costs/workflow_agent_cost_map_v1.md`
- `docs/runbooks/deploy_backend_and_frontend_ru.md`
- `docs/runbooks/no_ai_business_catalog_acceptance_ru.md`
- latest plans under `docs/superpowers/plans/2026-07-01-*`

Important status:

- Agent acceptance is mostly past the early roadmap state: Human Identity, Garment Identity, Material / Texture, Try-On Instruction, Quality Verifier, Repair Agent, image edit, Vertex Try-On smoke, service lifecycle, and deployed HTTP/worker Try-On smoke are documented as completed.
- Admin auth hardening and admin cost baseline are implemented/deployed on backend staging; Firebase reauth was the remaining frontend deploy issue at one point.
- B2B catalog, category gate, indexing, no-AI staging acceptance, Similar Search local catalog path, click events, analytics foundation, and candidate review foundation are documented as implemented or partially implemented.
- The current external blocker is provider billing/access: a paid staging catalog acceptance hit `403 PERMISSION_DENIED` with Google/Gemini billing/auth dunning. Until this is fixed, real Garment Identity validation, `/api/similar-search/garment-photo`, and paid AI acceptance are not reliable.
- Product billing/credits core exists separately from provider billing. Do not confuse Google provider billing restoration with changing live user credit prices.

---

## Files To Touch

Documentation only unless a verification step exposes a defect:

- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Modify: `docs/03_AGENT_SYSTEM_GUIDE.md`
- Modify: `docs/04_OWNER_REMAINING_WORK.md`
- Modify: `docs/costs/credits_pricing_table_v1.md`
- Create later if needed: `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md`
- Create later after 20-50 real runs: `docs/reports/YYYY-MM-DD-cost-recalibration-report.md`

Do not edit production workflow code during this plan unless a specific test fails and the root cause is confirmed.

---

### Task 1: Freeze The Pre-Billing Baseline

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Modify: `docs/04_OWNER_REMAINING_WORK.md`

- [x] Record the exact commit/working-tree state that will be deployed for post-billing tests.

Run:

```powershell
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
```

Expected:

- Dirty files are understood and intentionally included or excluded.
- No unknown temporary acceptance output is mistaken for source code.

- [x] Run the local backend verification gate.

Run:

```powershell
.venv\Scripts\python.exe scripts\check_architecture.py
.venv\Scripts\python.exe -m compileall -q src scripts
.venv\Scripts\python.exe -m pytest -q -x --maxfail=1
```

Expected:

- Architecture guardrail passes.
- Compileall passes.
- Full backend test suite passes or one failure is documented with exact root cause.

- [x] Run the local frontend verification gate.

Run:

```powershell
cd "C:\Code\Ai Fitfabrica\apps\web"
npm ci
npm run lint
npm run typecheck
npm run build
```

Expected:

- Lint, typecheck, and build pass.
- No frontend direct AI calls or credit calculations are introduced.

---

### Task 2: Restore Provider Billing And Access

**Owner:** human/operator, because this requires Google billing/account access.

**Files:**
- Modify only after completion: `docs/01_ACTION_LOG_CHECKLIST.md`

- [ ] Confirm Google Cloud billing is active for project `ai-fitfabrica`.
- [ ] Confirm the project can call Gemini/Google Gen AI and Vertex Virtual Try-On from the staging runtime identity.
- [ ] Confirm local CLI auth is interactive and not blocked by stale credentials.

Run:

```powershell
gcloud config set account admin@aisoulfabrica.com
gcloud config set project ai-fitfabrica
gcloud auth list
gcloud compute ssh ubuntu@fitfabrica-staging-vm --zone=europe-west1-b --command="echo SSH_READY"
```

Expected:

- SSH returns `SSH_READY`.
- No `cannot prompt during non-interactive execution`.
- Later paid provider calls no longer return `Lightning dunning decision is deny`.

---

### Task 3: Deploy The Verified Baseline To Staging

**Files:**
- Use: `docs/runbooks/deploy_backend_and_frontend_ru.md`
- Modify after completion: `docs/01_ACTION_LOG_CHECKLIST.md`

- [ ] Build the backend deploy archive.

Run:

```powershell
.\scripts\create_backend_deploy_archive.ps1 -OutputPath backend-deploy.tar.gz
Get-FileHash backend-deploy.tar.gz -Algorithm SHA256
```

Expected:

- Archive is created.
- Archive does not include `.env`, `.venv`, `.git`, frontend build output, or local secrets.

- [ ] Deploy backend to staging VM using the runbook.
- [ ] Verify backend health, worker health, and migration head.

Run:

```powershell
Invoke-WebRequest -UseBasicParsing "https://api.fit.aisoulfabrica.com/health"
```

Expected:

- Public health returns `200`.
- API and worker containers are healthy.
- Alembic is at head.
- Recent logs show no new tracebacks.

- [ ] Build and deploy frontend.

Run:

```powershell
cd "C:\Code\Ai Fitfabrica\apps\web"
$env:NEXT_PUBLIC_API_BASE_URL="https://api.fit.aisoulfabrica.com"
npm ci
npm run lint
npm run typecheck
npm run build
cd "C:\Code\Ai Fitfabrica"
firebase deploy --only hosting --project ai-fitfabrica
```

Expected:

- `https://fit.aisoulfabrica.com/` returns `200`.
- Key workspace/admin routes return `200` where public access is expected.
- Protected admin API routes return `403` without bearer token.

---

### Task 4: Run Provider Smoke Checks Before Full User Flows

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Create: `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md`

- [ ] Run a minimal live Garment Identity check.

Run:

```powershell
.venv\Scripts\python.exe scripts\garment_identity_live_acceptance.py
```

Expected:

- No provider billing/auth `403`.
- No burst `429` on a tiny run.
- False pass count remains `0`.

- [ ] Run a minimal live image edit smoke.

Run:

```powershell
.venv\Scripts\python.exe scripts\image_editing_live_smoke.py
```

Expected:

- Provider returns real image bytes.
- Output MIME type is `image/png`.
- Output object is persisted in object storage.

- [ ] Run a minimal live Vertex Try-On generation smoke.

Run:

```powershell
.venv\Scripts\python.exe scripts\try_on_generation_live_smoke.py
```

Expected:

- `generation_mode` is `vertex_virtual_try_on`.
- Result image artifact exists.
- Quality verifier verdict is `pass` or a documented fail-closed result.

---

### Task 5: Run Paid End-To-End Try-On Acceptance

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Create/update: `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md`

- [ ] Run service-level Try-On acceptance.

Run:

```powershell
.venv\Scripts\python.exe scripts\try_on_service_live_acceptance.py
```

Expected:

- Job reaches `completed` for a good input case.
- Status path includes analysis, generation, quality verification, and completion.
- Failed/blocked cases charge `0` credits.

- [ ] Run deployed HTTP/worker Try-On smoke.

Run:

```powershell
.venv\Scripts\python.exe scripts\try_on_http_worker_live_smoke.py --base-url "https://api.fit.aisoulfabrica.com"
```

Expected:

- API accepts upload.
- Worker executes the job.
- Final status is `completed` or a structured fail-closed status.
- Final result is not exposed before quality gate.

- [ ] Run full repair workflow acceptance.

Run:

```powershell
.venv\Scripts\python.exe scripts\repair_workflow_live_acceptance.py
```

Expected:

- Initial Quality Verifier recommends repair for local repairable defect.
- Repair Agent approves only local repair.
- Image edit produces real bytes.
- Second Quality Verifier returns `pass`.

---

### Task 6: Run Paid B2B Catalog And Similar Search Acceptance

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Create/update: `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md`

- [ ] Switch staging B2B category validation from sandbox/no-AI mode back to live provider mode.

Expected:

- `BUSINESS_CATALOG_CATEGORY_VALIDATION_MODE` is not `sandbox` for paid provider acceptance.
- Similar Search still uses its own Garment Identity wiring and does not inherit sandbox analyzer.

- [ ] Load a compact realistic catalog pack and run live admin category validation.

Expected:

- Product create, image upload, and submit-to-review pass.
- Admin category validation calls Garment Identity successfully.
- Matched products can be approved.
- Mismatched/uncertain products remain blocked.
- Search indexing marks approved products `indexed`.

- [ ] Run live `/api/similar-search/garment-photo` acceptance.

Expected:

- Garment photo upload validates type and size.
- Garment Identity invokes Gemini successfully.
- Response returns approved local catalog products first.
- Results include location ranking explanation and `image_url`.
- No hidden marketplace scraping is used.

- [ ] Verify click event and analytics path.

Expected:

- Product CTA records a backend click event.
- Local-only offers do not redirect to unsafe URLs.
- Admin analytics endpoint is read-only and requires bearer auth.

---

### Task 7: Verify Backend-Owned Product Billing/Credits

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Create/update: `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md`

- [ ] Confirm workspace bootstrap shows backend-provided credits and workflow costs.
- [ ] Confirm frontend does not calculate credits locally.
- [ ] Confirm successful paid workflows append ledger events through backend billing service.
- [ ] Confirm pre-generation failures, provider failures, quality rejects, and system repairs do not charge the user.

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_billing_domain_models.py tests\test_billing_policy.py tests\test_billing_service.py tests\test_credits_routes.py tests\test_try_on_billing_integration.py tests\test_b2b_billing_integration.py tests\architecture\test_billing_guardrails.py -q
```

Expected:

- Billing tests pass.
- Live billing policy is not changed by cost-map recommendations.
- Admin cost endpoint remains read-only.

---

### Task 8: Browser-Level Acceptance

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Create/update: `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md`

- [ ] Test public site navigation.
- [ ] Test `/workspace/try-on` upload, validation, disabled state, submit, status, result, and error state.
- [ ] Test `/workspace/similar-search` upload, location fields, empty state, success state, result CTA, and local-only offer behavior.
- [ ] Test `/workspace/business-catalog` product creation/import/upload state.
- [ ] Test `/admin/business-catalog` with bearer token: category validation, approve matched batch, indexing retry, review filters, analytics panel.
- [ ] Test `/workspace/credits` and verify displayed values come from backend bootstrap.

Expected:

- No `href="#"`.
- No fake AI status.
- No hardcoded credits/balance/user history.
- No browser-side AI provider calls.
- Loading, empty, error, success, validation, and disabled states are visible where applicable.

---

### Task 9: Run 20-50 Real Runs For Recalibration

**Files:**
- Create: `docs/reports/YYYY-MM-DD-cost-recalibration-report.md`
- Modify: `docs/costs/credits_pricing_table_v1.md` only after review approval
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`

- [ ] Run 20-50 real staging/prod workflow executions across:
  - Try-On success;
  - Try-On blocked before generation;
  - Try-On repair path;
  - Product Card;
  - Similar Search garment-photo;
  - B2B category validation.

- [ ] Export cost data from provider metadata, workflow cost events, and agent invocation ledger.
- [ ] Calculate:
  - actual average Try-On cost;
  - actual average Product Card cost;
  - repair rate;
  - retry rate;
  - failed free job cost;
  - provider `429`/`403`/timeout rate;
  - real margin by workflow.

Expected:

- Recalibration report exists.
- Pricing table changes are proposed separately and are not silently applied to live billing.

---

### Task 10: Final Go/No-Go Gate For Testing

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Modify: `docs/04_OWNER_REMAINING_WORK.md`

- [ ] Mark project ready for broader manual testing only when all are true:
  - local backend tests pass;
  - frontend lint/typecheck/build pass;
  - staging deploy passes;
  - provider smoke checks pass;
  - Try-On HTTP/worker smoke passes;
  - repair workflow passes;
  - B2B category validation and indexing pass;
  - Similar Search garment-photo pass;
  - billing guardrails pass;
  - admin routes require bearer token;
  - no hidden scraping is enabled;
  - VM is cleaned or intentionally running for scheduled testing.

Expected final status:

```text
Ready for controlled manual testing after billing restoration.
```

If any item fails, record:

- exact command or page;
- exact HTTP/status/error;
- whether user was charged;
- root cause;
- fix owner;
- retest command.
