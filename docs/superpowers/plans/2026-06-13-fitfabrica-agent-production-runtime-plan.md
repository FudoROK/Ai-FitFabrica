# FitFabrica Production Agent Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the current web/backend baseline, then turn the existing typed agent packages into a production backend-controlled agent runtime, starting with one complete image Try-On workflow.

**Architecture:** FastAPI workflows remain the only orchestrator. Agents receive backend-approved context and return validated structured intents; they never persist canonical state, charge credits, choose retries, or call each other directly. Image generation, editing, storage, embeddings, and marketplace connectors remain provider-neutral backend tools behind ports.

**Tech Stack:** FastAPI, Pydantic, PostgreSQL, Redis, S3-compatible object storage, Qdrant, Google ADK, Gemini on Vertex AI, Vertex Virtual Try-On, Vertex image editing/generation adapters, Next.js, Firebase Hosting.

---

## 1. Current Truth

### Deployment state on 2026-06-14

- Public frontend answers at `https://fit.aisoulfabrica.com`.
- Public backend answers at `https://api.fit.aisoulfabrica.com`.
- The portable staging runtime has the current baseline and Wave 1 canonical agent gateway.
- API and worker health checks pass, migration `20260614_000011` is at head, and the `agent_invocations` audit table exists.
- Operator authentication for GCP and Firebase is active.

### Agent state

The repository already contains 15 product-agent packages under `src/adk_agents/`:

- `orchestrator_agent`
- `user_profile_agent`
- `business_profile_agent`
- `human_identity_agent`
- `garment_identity_agent`
- `material_texture_agent`
- `try_on_agent`
- `quality_verifier_agent`
- `repair_agent`
- `fashion_stylist_agent`
- `marketplace_agent`
- `trend_agent`
- `pricing_agent`
- `product_card_agent`
- `cost_credits_agent`

Each package already has `agent.py`, `contracts.py`, `prompt_config.py`, and `deploy_config.py`. This is a good typed foundation, but it is not yet the final production runtime:

- prompts are intentionally minimal;
- workflow-specific request contracts are incomplete;
- the Try-On workflow does not call the reasoning agents in its execution chain;
- image generation/editing providers still include stub implementations;
- no agent invocation ledger, prompt version, or evaluation gate is persisted.

## 2. Non-Negotiable Runtime Rules

1. Backend owns orchestration, job status, persistence, retry, repair, billing, and final decisions.
2. Agents return structured JSON only.
3. Agents do not call each other directly. A2A is not introduced without separate explicit user approval.
4. Agents do not receive database, billing, queue, or unrestricted network tools.
5. Every agent output is validated by a strict Pydantic contract before workflow use.
6. Every invocation records agent name, contract version, prompt version, provider, model, latency, cost metadata, confidence, and validation result.
7. Image generation and editing are tools/adapters, not autonomous agents.
8. Provider selection stays behind ports so Gemini/Vertex can later be replaced without changing workflows.

## 3. Production Interaction Model

```text
Frontend
  -> FastAPI route validates DTO
  -> Backend creates durable job
  -> Worker claims job
  -> Backend workflow loads approved artifacts and context
  -> Backend invokes one agent through AgentGateway
  -> Agent returns typed structured output
  -> Backend validates and persists invocation result
  -> Backend invokes provider tool when required
  -> Backend invokes Quality Verifier
  -> Backend decides pass / repair / retry / reject
  -> Backend records credits and final state
  -> Frontend polls status and displays result
```

Agent-to-agent interaction is always mediated by backend workflow state:

```text
Human Identity output \
Garment Identity output  -> Backend Try-On workflow -> Try-On instruction output
Material output         /                         -> Generation tool
                                                   -> Quality Verifier output
                                                   -> Backend decision
                                                   -> Repair Agent output -> Editing tool
```

## 4. Agent Prompt Standard

Every `prompt_config.py` must contain the following explicit sections:

1. **Role:** one narrow responsibility.
2. **Authoritative inputs:** which backend fields and artifacts may be used.
3. **Required analysis:** exact attributes the agent must inspect.
4. **Allowed decisions:** the limited decisions the agent may suggest.
5. **Forbidden actions:** persistence, billing, retry decisions, hidden assumptions, direct agent calls.
6. **Output contract:** exact structured schema and enum values.
7. **Confidence policy:** confidence per important conclusion, not one decorative score.
8. **Evidence policy:** every claim must refer to visible/provided evidence.
9. **Uncertainty policy:** unknown values must be reported as unknown.
10. **Safety policy:** no biometric identity claims, protected-attribute inference, or invented product facts.

Required prompt-version format:

```python
AGENT_NAME = "human_identity"
PROMPT_VERSION = "human_identity.v1"
CONTRACT_VERSION = "human_identity.contract.v1"
```

## 5. Image Workflow Agents And Providers

### Human Identity Agent

**Purpose:** Analyze preservation constraints, not identify the person.

**Prompt must request:**

- face visibility and occlusion;
- pose and camera angle;
- visible body regions;
- silhouette/proportion preservation constraints;
- lighting and background constraints;
- limitations caused by crop, blur, or occlusion.

**Must forbid:**

- naming or identifying a person;
- ethnicity, health, age, or other sensitive inference;
- inventing hidden body details.

**Recommended reasoning provider:** Gemini multimodal through Vertex AI. Use a fast model for normal jobs and a stronger model only for low-confidence escalation.

### Garment Identity Agent

**Purpose:** Build the canonical visual garment specification.

**Prompt must request:**

- category and silhouette;
- dominant and secondary colors;
- collar, sleeves, pockets, buttons, closures;
- print, logo, trim, seams;
- visible texture and drape;
- must-preserve details;
- ambiguity and limitations.

**Recommended reasoning provider:** Gemini multimodal through Vertex AI.

### Material / Texture Agent

**Purpose:** Describe visible material behavior honestly.

**Prompt must request:**

- visible weave/knit/finish;
- gloss, transparency, stiffness, drape;
- evidence source;
- confidence and alternative interpretations.

**Must forbid:** claiming exact fiber composition unless a trusted label or product description is supplied.

### Try-On Instruction Agent

**Purpose:** Convert approved analyses into a typed generation instruction.

**Prompt must request:**

- human preservation constraints;
- garment preservation constraints;
- fit and layering intent;
- generation exclusions;
- expected framing;
- quality-critical details.

**Must not generate images.**

### Image Generation Tool

This is a backend adapter, not an agent.

**Preferred first provider:** Vertex Virtual Try-On for person + garment composition.

**Fallback policy:**

- no silent fallback in production;
- fallback is allowed only by explicit environment policy;
- every provider attempt and artifact is persisted;
- user is not charged again for system-caused retries.

### Quality Verifier Agent

**Purpose:** Compare source artifacts with generated output and return evidence-driven defects.

**Prompt must request separate scores for:**

- face preservation;
- body/pose preservation;
- garment shape and details;
- color fidelity;
- texture consistency;
- hands/neck/waist artifacts;
- background artifacts;
- realism.

**Output:** defect list with severity, evidence, repairability, confidence, and recommended action. Backend maps that recommendation to the final action.

**Recommended reasoning provider:** a strong Gemini multimodal model, because this gate controls whether an image reaches the user.

### Repair Agent

**Purpose:** Create a narrow repair plan from approved verifier defects.

**Prompt must request:**

- repair mask/region intent;
- details that must remain unchanged;
- ordered edit instructions;
- conditions when local repair is unsafe.

**Image editing tool:** provider-neutral `ImageEditingPort`, initially backed by a Vertex image-editing implementation. The agent plans; the adapter edits.

### Fashion Stylist Agent

**Purpose:** Produce a practical explanation only after the image passes quality.

**Prompt must request:** fit observations, color/proportion reasoning, occasion guidance, and concise actionable tips. It must not claim that a generated image proves real-world sizing.

## 6. Non-Image Agents

### Orchestrator Agent

- Classifies user intent into an allow-listed workflow.
- Returns required inputs and missing inputs.
- Never starts jobs or invokes agents.
- Backend validates the proposed workflow against capabilities and permissions.

### User Profile Agent

- Converts explicit B2C preferences/history into a typed profile patch proposal.
- Backend validates and persists accepted fields.
- Must distinguish explicit facts from inferred preferences.

### Business Profile Agent

- Converts seller-provided information into typed brand/channel/content rules.
- Must not invent marketplace policies or business metrics.

### Marketplace Agent

- Receives normalized catalog/search evidence from backend connectors.
- May propose retrieval intent, filters, and comparison axes.
- Gets read-only approved connector tools only.
- Must never scrape hidden sources or produce offers without backend evidence.

### Pricing Agent

- Receives backend-calculated comparable ranges, costs, and margins.
- Explains positioning and proposes a price range.
- Backend remains authoritative for numeric calculations and final price.

### Product Card Agent

- Produces typed title, description, characteristics, and channel-specific content from approved product facts.
- Must mark unsupported attributes as unknown.

### Trend Agent

- Converts approved trend signals into practical recommendations.
- Does not claim a trend without source metadata and freshness timestamp.

### Cost / Credits Agent

- Explains backend-calculated cost components.
- Never calculates balances, writes ledger events, or decides charges.

## 7. Implementation Waves

### Wave 0: Deploy Current Baseline

**Files:**

- Verify: `docker-compose.portable-staging.yml`
- Verify: `.env.portable-remote-staging.local`
- Verify: `apps/web/.env.local`
- Use: `scripts/deploy_portable_runtime.sh`
- Use: `firebase.json`

- [x] Reauthenticate the approved operator accounts:
  - `gcloud auth login`
  - `gcloud config set account admin@aisoulfabrica.com`
  - `firebase login --reauth`
  - `firebase login:use admin@aisoulfabrica.com`
- [x] Confirm the GCP VM name, zone, public IP, and SSH source restriction.
- [x] Upload/sync the current deployment baseline to `/opt/fitfabrica` without copying local secrets or caches.
- [x] Preserve the remote `.env.portable-remote-staging.local`.
- [x] Run the portable platform smoke check.
- [x] Deploy the portable runtime.
- [x] Verify migrations, API health, worker health, and `/api/workspace/bootstrap`.
- [x] Build `apps/web` with `NEXT_PUBLIC_API_BASE_URL=https://api.fit.aisoulfabrica.com`.
- [x] Deploy Firebase Hosting for project `ai-fitfabrica`.
- [x] Verify public frontend and backend availability, workspace bootstrap, CORS, and text encoding.

### Wave 1: Canonical Agent Gateway

**Files:**

- Create: `src/domain/agent_runtime.py`
- Create: `src/use_cases/agents/ports.py`
- Create: `src/use_cases/agents/invocation_service.py`
- Create: `src/adapters/agents/adk_agent_gateway.py`
- Create: `src/adapters/database/sql/agent_invocation_models.py`
- Create: `src/adapters/database/sql/agent_invocation_repositories.py`
- Modify: `src/entrypoints/runtime_dependency_contracts.py`
- Modify: `src/entrypoints/runtime_dependency_foundation_builders.py`
- Test: `tests/test_agent_invocation_service.py`
- Test: `tests/test_agent_invocation_sql_repository.py`
- Test: `tests/architecture/test_agent_runtime_guardrails.py`

- [x] Define typed request/result/envelope models with agent, prompt, contract, provider, model, trace, latency, confidence, and validation metadata.
- [x] Add a single `AgentInvocationPort`; workflows must not import ADK agent roots.
- [x] Implement strict validation, timeout, redaction, and typed failure mapping.
- [x] Persist invocation audit records without storing raw secrets or unrestricted image bytes.
- [x] Add architecture tests forbidding direct agent calls from routes and cross-agent imports.

### Wave 2: Prompt And Contract Hardening

Image-workflow slice completed on `2026-06-14`. Non-image agent hardening remains aligned with the workflows that connect them in Waves 4-5.

**Files:**

- Modify: every `src/adk_agents/*/contracts.py`
- Modify: every `src/adk_agents/*/prompt_config.py`
- Modify: every `src/adk_agents/*/deploy_config.py`
- Test: `tests/test_fitfabrica_agent_contracts.py`
- Create: `tests/test_agent_prompt_policy.py`
- Create: `tests/fixtures/agent_evaluations/`

- [x] Add request contracts, not only response contracts, for the seven image-workflow agents.
- [x] Add prompt and contract versions for the seven image-workflow agents.
- [x] Replace free-form strings with enums and typed defect/evidence objects where image-workflow decisions depend on them.
- [x] Add golden evaluation fixtures for valid, ambiguous, unsafe, and malformed image-analysis inputs.
- [x] Add output-repair policy only for transport formatting failures; semantic failures return typed errors.

### Wave 3: First Real End-To-End Try-On Agent Workflow

Human Identity Agent isolated enterprise slice completed and deployed to staging on `2026-06-14`: canonical invocation, fail-closed backend policy, durable Try-On analysis persistence, mandatory pre-generation gate, approved artifact integrity checks, and real multimodal Gemini delivery through `gemini-2.5-flash`. Text and synthetic-image multimodal staging smoke calls passed. Visual-accuracy acceptance remains gated on an approved staging evaluation image set.

**Files:**

- Modify: `src/use_cases/try_on/workflow_execution.py`
- Modify: `src/use_cases/try_on/workflow_service.py`
- Modify: `src/use_cases/try_on/ports.py`
- Create: `src/use_cases/try_on/agent_analysis_service.py`
- Create: `src/adapters/try_on/vertex_virtual_try_on_generation.py`
- Create: `src/adapters/try_on/vertex_image_editing.py`
- Modify: `src/entrypoints/runtime_dependency_workflow_builders.py`
- Test: `tests/test_try_on_agent_analysis_service.py`
- Test: `tests/test_try_on_agent_workflow.py`
- Test: `tests/test_try_on_quality_repair_policy.py`

- [x] Invoke Human Identity, Garment Identity, and Material agents in parallel after upload validation.
- [x] Persist their validated outputs against the job.
- [x] Invoke Try-On Instruction Agent with only approved outputs.
- [x] Execute generation through `TryOnGenerationPort`.
- [ ] Invoke Quality Verifier with source and result artifacts.
- [ ] Let backend decide pass, repair, retry, reject, or request better input.
- [ ] Invoke Repair Agent only for local repairable defects, then execute `ImageEditingPort`.
- [ ] Re-run Quality Verifier after repair.
- [ ] Invoke Fashion Stylist only after final quality pass.
- [ ] Record credits only from backend billing policy.

### Wave 4: Profiles And Routing

**Files:**

- Create: `src/use_cases/agents/orchestration_service.py`
- Modify: `src/use_cases/workspace/`
- Modify: `src/entrypoints/workspace_routes.py`
- Test: `tests/test_agent_orchestration_service.py`
- Test: `tests/test_profile_agent_workflows.py`

- [ ] Introduce Orchestrator Agent as a routing adviser, not executor.
- [ ] Validate its workflow suggestion against backend allow-lists and user capability state.
- [ ] Connect User Profile and Business Profile agents to backend-owned patch approval services.
- [ ] Persist explicit facts separately from inferred preferences.

### Wave 5: B2B And Commerce Agents

**Files:**

- Modify: `src/use_cases/product_card/`
- Modify: `src/use_cases/content_package/`
- Modify: `src/use_cases/similar_search/`
- Modify: `src/use_cases/pricing/`
- Create: `src/use_cases/trends/`
- Test: corresponding workflow and agent integration suites.

- [ ] Connect Product Card Agent to product-card workflow.
- [ ] Connect Marketplace Agent only through approved connector results.
- [ ] Connect Pricing Agent after backend computes comparable ranges and margins.
- [ ] Connect Trend Agent only to timestamped approved signals.
- [ ] Connect Cost/Credits Agent only to backend-calculated charge explanations.

### Wave 6: Production Operations And Evaluation

**Files:**

- Create: `src/use_cases/agents/evaluation_service.py`
- Create: `scripts/run_agent_evaluations.py`
- Modify: `src/entrypoints/status_routes.py`
- Modify: deployment env examples and runbooks.
- Test: `tests/test_agent_evaluation_service.py`
- Test: `tests/test_agent_runtime_health.py`

- [ ] Add per-agent latency, error-rate, invalid-output-rate, and confidence metrics.
- [ ] Add prompt/model canary configuration.
- [ ] Add offline evaluation gates before prompt or model promotion.
- [ ] Add cost ceilings and circuit breakers.
- [ ] Add runtime health that distinguishes backend health from individual provider health.
- [ ] Document rollback for model, prompt, and provider changes.

## 8. Required Test Gates

Every wave must pass:

```powershell
.venv\Scripts\python.exe scripts\check_architecture.py
.venv\Scripts\python.exe -m compileall src
.venv\Scripts\python.exe -m pytest -q
cd apps/web
npm run lint
npm run typecheck
npm run build
```

Agent-specific release gates:

- strict contract validation is `100%`;
- no malformed output reaches a workflow;
- no direct agent-to-agent imports;
- no direct DB/billing/queue tool access from agents;
- quality verifier false-pass rate is measured on an approved evaluation set;
- repair is allowed only for explicitly repairable defects;
- real image generation is disabled in production until capability evaluation is approved.

## 9. Recommended Delivery Order

1. Unblock credentials and deploy the already verified current baseline.
2. Implement canonical Agent Gateway and invocation ledger.
3. Harden prompts/contracts for the seven image workflow agents.
4. Deliver one real Try-On workflow end to end.
5. Evaluate quality and repair reliability using a controlled dataset.
6. Add routing/profile agents.
7. Add B2B, marketplace, pricing, trend, and cost explanation agents.
8. Enable production image generation only after quality, cost, and rollback gates pass.

## 10. Exit Criteria

The agent layer is production-ready only when:

- workflows invoke agents exclusively through the canonical gateway;
- every agent has versioned request, response, prompt, and deploy contracts;
- backend owns every side effect and final decision;
- one real Try-On workflow passes end-to-end staging verification;
- image output cannot reach a user without quality verification;
- provider/model changes pass offline evaluation before promotion;
- deployment, monitoring, cost limits, and rollback are documented and tested.
