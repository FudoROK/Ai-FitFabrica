# FitFabrica Agent System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current legacy and infrastructure-shaped ADK contour with an explicit FitFabrica product-agent system whose contracts, prompts, and deploy packages map directly to backend-owned workflows.

**Architecture:** Keep orchestration in backend workflow code. Product agents return structured outputs only. They do not create jobs, choose retries, mutate billing state, persist truth, or call each other directly. Existing memory-support agents remain infrastructure-only where they are still needed, while generic `primary_agent` logic is split into FitFabrica-specific agent packages.

**Tech Stack:** Python, Google ADK, Gemini/Vertex as the first provider implementation, backend-owned provider runtime, FastAPI, PostgreSQL, Redis, S3-compatible object storage, Qdrant, pytest.

---

## Scope And Baseline

Current state in this worktree:

- `src/adk_agents` contains:
  - `primary_agent`
  - `daily_memory_agent`
  - `rolling_memory_agent`
  - `daily_memory_agent_tmp20260425_024853`
- `tests/test_adk_agent_root_contract.py` still verifies only those legacy roots.
- Product workflows already exist in backend code for:
  - Try-On
  - similar search
  - product card
  - content package
  - pricing
  - billing
  - operations / worker runtime
- Provider abstraction already exists through:
  - `src/domain/provider_ports.py`
  - `src/llm/provider_runtime.py`
- Try-On already has backend-owned quality, repair, and stylist contours, but they are adapter-shaped rather than product-agent-packaged.
- The portable platform baseline is already fixed and is not part of this stage.

This stage does:

- define the target `src/adk_agents` structure for FitFabrica
- split infrastructure-support agents from product agents
- define product-agent contracts for the approved FitFabrica roles
- decide the landing order so B2C Try-On agents ship first
- align runtime wiring so agents stay structured-output only
- prepare cleanup of temporary / legacy agent folders

This stage does not:

- redesign backend workflow ownership
- move orchestration into ADK
- bypass provider-neutral ports
- turn every workflow into a live ADK invocation on day one
- finalize deployment topology for agent runtimes beyond approved deploy configs

## Architecture Rules For This Stage

The following constraints are mandatory:

- backend workflows remain the sole orchestrator
- agents may analyze, classify, rank, and explain
- agents may not persist canonical truth directly
- agents may not charge credits directly
- agents may not choose final repair / retry / reject outcomes
- agents may not call each other directly through hidden chains
- all agent outputs must be typed and backend-consumable
- every agent package must declare its contract, prompt config, and deploy config explicitly

## Target Agent Topology

### Infrastructure-Support Agents That Remain

These remain as support-only contours, not product agents:

- `daily_memory_agent`
- `rolling_memory_agent`

Their role stays limited to memory summarization / support-runtime concerns.

### Legacy Or Temporary Agents To Remove Or Archive

These are not target architecture:

- `daily_memory_agent_tmp20260425_024853`
- `primary_agent`

`primary_agent` is considered a migration-state generic agent. Its responsibilities must be split into approved FitFabrica product-agent roles.

### Target Product-Agent Packages

The target `src/adk_agents` structure should converge on packages like:

- `src/adk_agents/orchestrator_agent`
- `src/adk_agents/user_profile_agent`
- `src/adk_agents/business_profile_agent`
- `src/adk_agents/human_identity_agent`
- `src/adk_agents/garment_identity_agent`
- `src/adk_agents/material_texture_agent`
- `src/adk_agents/try_on_agent`
- `src/adk_agents/fashion_stylist_agent`
- `src/adk_agents/marketplace_agent`
- `src/adk_agents/trend_agent`
- `src/adk_agents/pricing_agent`
- `src/adk_agents/quality_verifier_agent`
- `src/adk_agents/repair_agent`
- `src/adk_agents/cost_credits_agent`

Each package should eventually expose:

- `agent.py`
- `contracts.py`
- `prompt_config.py`
- `deploy_config.py`
- `__init__.py`

## Product-Agent Contract Package

### 1. Orchestrator Agent

Purpose:

- interpret user intent at the product/workflow-routing level
- suggest workflow type and required supporting context

Must return structured fields such as:

- `workflow_type`
- `requested_capabilities`
- `required_inputs`
- `confidence`
- `limitations`

Must not:

- enqueue jobs
- invoke other agents directly
- persist workflow state

### 2. User Profile Agent

Purpose:

- summarize B2C profile, style preferences, fit preferences, budget, and history into backend-usable structured output

Primary backend consumers:

- Try-On
- outfit recommendation
- cheaper/similar alternatives

### 3. Business Profile Agent

Purpose:

- summarize seller / merchant style, target channel, content rules, and business context into backend-usable structured output

Primary backend consumers:

- product card
- content package
- pricing

### 4. Human Identity Agent

Purpose:

- identify face/body/pose attributes that must stay stable in Try-On or related image workflows

Primary backend consumers:

- Try-On workflow service
- quality verifier
- repair contour

### 5. Garment Identity Agent

Purpose:

- extract clothing attributes that must remain stable

Primary backend consumers:

- Try-On
- similar search
- product card
- pricing

### 6. Material / Texture Agent

Purpose:

- estimate visible material and texture signals honestly
- report uncertainty explicitly

Primary backend consumers:

- Try-On
- product card
- similar search

### 7. Try-On Agent

Purpose:

- convert human, garment, and style constraints into structured generation instructions for the backend-owned generation path

Primary backend consumers:

- Try-On workflow service

### 8. Fashion Stylist Agent

Purpose:

- generate user-facing fit/style explanation and outfit reasoning

Primary backend consumers:

- Try-On result completion
- future outfit recommendation contour

### 9. Marketplace Agent

Purpose:

- transform garment/product intent into retrieval and comparison guidance over approved marketplace data

Primary backend consumers:

- similar search
- cheaper alternative ranking

### 10. Trend Agent

Purpose:

- turn trend signals into practical, structured recommendations

Primary backend consumers:

- future recommendation and B2B content workflows

### 11. Pricing Agent

Purpose:

- explain pricing position and recommendation rationale from backend-prepared evidence

Primary backend consumers:

- pricing workflow

### 12. Quality Verifier Agent

Purpose:

- interpret backend-owned verification facts and return structured pass / repair / reject reasoning

Primary backend consumers:

- Try-On quality stage
- future product-image quality stages

### 13. Repair Agent

Purpose:

- transform localized defect evidence into structured repair instructions for backend-owned editing paths

Primary backend consumers:

- Try-On repair stage

### 14. Cost / Credits Agent

Purpose:

- explain cost composition or economic rationale in structured form when needed

Primary backend consumers:

- billing explanation surfaces
- internal operations / audit

This agent does not own charging logic. Backend billing code remains authoritative.

## Execution Priority

Implementation order must follow business priority, not abstract completeness.

### Wave 1: B2C Try-On Agents

Implement first:

- `human_identity_agent`
- `garment_identity_agent`
- `material_texture_agent`
- `try_on_agent`
- `quality_verifier_agent`
- `repair_agent`
- `fashion_stylist_agent`

Reason:

- Try-On is the primary B2C workflow already closest to production shape.

### Wave 2: Workflow Routing And Profiles

Implement second:

- `orchestrator_agent`
- `user_profile_agent`
- `business_profile_agent`

Reason:

- these agents improve routing and personalization across multiple workflows once the first Try-On agent contour is stable.

### Wave 3: Search / Pricing / Marketplace Expansion

Implement third:

- `marketplace_agent`
- `pricing_agent`
- `trend_agent`
- `cost_credits_agent`

Reason:

- these depend on the already-built similar-search, pricing, and billing contours and are lower priority than Try-On completion.

## File Structure

New and changed files should stay split by responsibility:

- `src/adk_agents/__init__.py`
  - export only approved stable agent contracts
- `src/adk_agents/<agent_name>/agent.py`
  - one ADK root agent package per approved role
- `src/adk_agents/<agent_name>/contracts.py`
  - typed request / response contract definitions
- `src/adk_agents/<agent_name>/prompt_config.py`
  - approved instructions and schema bindings
- `src/adk_agents/<agent_name>/deploy_config.py`
  - deployment/runtime metadata for the first provider implementation
- `src/entrypoints/runtime_dependencies.py`
  - provider-runtime-backed agent construction only through composition root
- `src/use_cases/*`
  - backend workflow code remains the caller/orchestrator
- `tests/test_adk_agent_root_contract.py`
  - update to reflect approved roots
- `tests/test_fitfabrica_agent_contracts.py`
  - verify typed product-agent contract payloads
- `tests/test_fitfabrica_agent_runtime_wiring.py`
  - verify agent runtime wiring through backend composition root
- `tests/architecture/test_fitfabrica_agent_guardrails.py`
  - enforce no direct orchestration leakage into agents
- `docs/project_description.md`
  - record the product-agent baseline
- `docs/project_structure.md`
  - record the target `src/adk_agents` topology
- `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`
  - mark Stage 11 planning complete

## Task 1: Freeze The Approved Agent Topology

**Files:**
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/project_description.md`
- Create: `tests/test_fitfabrica_agent_plan_docs.py`

- [ ] **Step 1: Write the failing documentation test**

The test should assert that:

- the new Stage 11 plan exists
- the master plan references it
- the target agent package names are listed

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_plan_docs.py -q
```

Expected: FAIL because the dedicated agent-system plan and doc references do not exist yet.

- [ ] **Step 3: Align master and architecture docs to the approved topology**

Document:

- support-only memory agents
- temporary/legacy agent folders
- target FitFabrica product-agent package list

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_plan_docs.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-06-02-fitfabrica-agent-system-plan.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md docs/project_structure.md docs/project_description.md tests/test_fitfabrica_agent_plan_docs.py
git commit -m "docs: define fitfabrica agent system plan"
```

## Task 2: Replace Legacy Root Contracts With FitFabrica Agent Contracts

**Files:**
- Create: `tests/test_fitfabrica_agent_contracts.py`
- Create: `src/adk_agents/human_identity_agent/contracts.py`
- Create: `src/adk_agents/garment_identity_agent/contracts.py`
- Create: `src/adk_agents/material_texture_agent/contracts.py`
- Create: `src/adk_agents/try_on_agent/contracts.py`
- Create: `src/adk_agents/quality_verifier_agent/contracts.py`
- Create: `src/adk_agents/repair_agent/contracts.py`
- Create: `src/adk_agents/fashion_stylist_agent/contracts.py`
- Modify: `src/adk_agents/__init__.py`

- [ ] **Step 1: Write the failing contract tests**

Start with Wave 1 agent contracts only.

The tests should assert that each contract:

- is typed
- exposes explicit confidence / limitation fields where applicable
- can be consumed by backend workflows without free-form parsing

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_contracts.py -q
```

Expected: FAIL because the FitFabrica product-agent contracts do not exist yet.

- [ ] **Step 3: Implement Wave 1 product-agent contracts**

Add typed contracts for:

- human identity
- garment identity
- material / texture
- Try-On generation instructions
- quality-verifier decision
- repair instructions
- stylist note generation

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_contracts.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adk_agents/__init__.py src/adk_agents/human_identity_agent/contracts.py src/adk_agents/garment_identity_agent/contracts.py src/adk_agents/material_texture_agent/contracts.py src/adk_agents/try_on_agent/contracts.py src/adk_agents/quality_verifier_agent/contracts.py src/adk_agents/repair_agent/contracts.py src/adk_agents/fashion_stylist_agent/contracts.py tests/test_fitfabrica_agent_contracts.py
git commit -m "feat: add fitfabrica wave1 agent contracts"
```

## Task 3: Add Wave 1 Agent Packages And Roots

**Files:**
- Create: `src/adk_agents/human_identity_agent/agent.py`
- Create: `src/adk_agents/human_identity_agent/prompt_config.py`
- Create: `src/adk_agents/human_identity_agent/deploy_config.py`
- Repeat for:
  - `garment_identity_agent`
  - `material_texture_agent`
  - `try_on_agent`
  - `quality_verifier_agent`
  - `repair_agent`
  - `fashion_stylist_agent`
- Modify: `tests/test_adk_agent_root_contract.py`

- [ ] **Step 1: Write the failing root-export tests**

The tests should verify that the approved Wave 1 agent packages export `BaseAgent` roots.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_adk_agent_root_contract.py -q
```

Expected: FAIL because the test still references only legacy roots.

- [ ] **Step 3: Implement the Wave 1 agent packages**

Each package must include:

- `agent.py`
- `contracts.py`
- `prompt_config.py`
- `deploy_config.py`
- `__init__.py`

Prompt/config files must stay role-specific and structured-output-first.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_adk_agent_root_contract.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adk_agents/human_identity_agent src/adk_agents/garment_identity_agent src/adk_agents/material_texture_agent src/adk_agents/try_on_agent src/adk_agents/quality_verifier_agent src/adk_agents/repair_agent src/adk_agents/fashion_stylist_agent tests/test_adk_agent_root_contract.py
git commit -m "feat: add fitfabrica wave1 adk agent packages"
```

## Task 4: Wire Wave 1 Agents Through Backend Composition Root

**Files:**
- Modify: `src/entrypoints/runtime_dependencies.py`
- Create: `tests/test_fitfabrica_agent_runtime_wiring.py`
- Modify: `src/use_cases/try_on/workflow_service.py` only if contract injection points are needed

- [ ] **Step 1: Write the failing runtime-wiring tests**

The tests should verify that:

- Wave 1 agent packages are constructed through runtime dependencies
- Try-On workflow code receives agent outputs through typed boundaries
- backend code remains authoritative for workflow transitions

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_runtime_wiring.py -q
```

Expected: FAIL because FitFabrica-specific agent runtime wiring does not exist yet.

- [ ] **Step 3: Implement composition-root wiring**

Backend runtime wiring should:

- build agent runtime clients through the provider runtime layer
- inject typed adapters into Try-On workflow boundaries
- avoid direct imports from route handlers into individual ADK packages

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_runtime_wiring.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/runtime_dependencies.py src/use_cases/try_on/workflow_service.py tests/test_fitfabrica_agent_runtime_wiring.py
git commit -m "feat: wire fitfabrica wave1 agents through backend runtime"
```

## Task 5: Add Guardrails And Archive Legacy Agent Paths

**Files:**
- Create: `tests/architecture/test_fitfabrica_agent_guardrails.py`
- Modify: `src/adk_agents/__init__.py`
- Modify or remove:
  - `src/adk_agents/primary_agent`
  - `src/adk_agents/daily_memory_agent_tmp20260425_024853`

- [ ] **Step 1: Write the failing guardrail tests**

The tests should enforce:

- no direct orchestration logic inside product-agent packages
- no hidden direct agent-to-agent imports across product-agent packages
- temporary agent folders are no longer treated as active runtime surfaces

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/architecture/test_fitfabrica_agent_guardrails.py -q
```

Expected: FAIL because the old agent layout is still active.

- [ ] **Step 3: Narrow or archive legacy agents**

Apply the approved split:

- keep `daily_memory_agent` and `rolling_memory_agent` as support-only
- archive or remove `daily_memory_agent_tmp20260425_024853`
- remove `primary_agent` from active architecture

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/architecture/test_fitfabrica_agent_guardrails.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/architecture/test_fitfabrica_agent_guardrails.py src/adk_agents
git commit -m "test: enforce fitfabrica agent system boundaries"
```

## Task 6: Add Wave 2 Routing And Profile Agents

**Files:**
- Create:
  - `src/adk_agents/orchestrator_agent/*`
  - `src/adk_agents/user_profile_agent/*`
  - `src/adk_agents/business_profile_agent/*`
- Extend:
  - `tests/test_fitfabrica_agent_contracts.py`
  - `tests/test_adk_agent_root_contract.py`
  - `tests/test_fitfabrica_agent_runtime_wiring.py`

- [ ] **Step 1: Write the failing Wave 2 tests**

The tests should assert typed contracts and root exports for:

- orchestrator
- user profile
- business profile

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_contracts.py tests/test_adk_agent_root_contract.py tests/test_fitfabrica_agent_runtime_wiring.py -q
```

Expected: FAIL because Wave 2 agents do not exist yet.

- [ ] **Step 3: Implement Wave 2 packages and runtime wiring**

Keep outputs structured and workflow-safe.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_contracts.py tests/test_adk_agent_root_contract.py tests/test_fitfabrica_agent_runtime_wiring.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adk_agents/orchestrator_agent src/adk_agents/user_profile_agent src/adk_agents/business_profile_agent tests/test_fitfabrica_agent_contracts.py tests/test_adk_agent_root_contract.py tests/test_fitfabrica_agent_runtime_wiring.py
git commit -m "feat: add fitfabrica wave2 routing and profile agents"
```

## Task 7: Add Wave 3 Search / Pricing / Commerce Agents

**Files:**
- Create:
  - `src/adk_agents/marketplace_agent/*`
  - `src/adk_agents/trend_agent/*`
  - `src/adk_agents/pricing_agent/*`
  - `src/adk_agents/cost_credits_agent/*`
- Extend tests and docs accordingly

- [ ] **Step 1: Write the failing Wave 3 tests**

The tests should assert typed contracts and root exports for:

- marketplace
- trend
- pricing
- cost / credits

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_contracts.py tests/test_adk_agent_root_contract.py tests/test_fitfabrica_agent_runtime_wiring.py -q
```

Expected: FAIL because Wave 3 agents do not exist yet.

- [ ] **Step 3: Implement Wave 3 packages**

Keep them backend-owned and evidence-driven.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_contracts.py tests/test_adk_agent_root_contract.py tests/test_fitfabrica_agent_runtime_wiring.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adk_agents/marketplace_agent src/adk_agents/trend_agent src/adk_agents/pricing_agent src/adk_agents/cost_credits_agent tests/test_fitfabrica_agent_contracts.py tests/test_adk_agent_root_contract.py tests/test_fitfabrica_agent_runtime_wiring.py
git commit -m "feat: add fitfabrica wave3 commerce agents"
```

## Task 8: Final Regression And Documentation Alignment

**Files:**
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Update docs for the FitFabrica product-agent baseline**

Document:

- support-only memory agents
- product-agent package topology
- Wave 1 / Wave 2 / Wave 3 landing order
- backend orchestration boundaries

- [ ] **Step 2: Run targeted agent-system verification**

Run:

```bash
python -m pytest tests/test_fitfabrica_agent_plan_docs.py tests/test_fitfabrica_agent_contracts.py tests/test_fitfabrica_agent_runtime_wiring.py tests/test_adk_agent_root_contract.py tests/architecture/test_fitfabrica_agent_guardrails.py -q
```

Expected: PASS

- [ ] **Step 3: Run broader workflow regression**

Run:

```bash
python -m pytest tests/test_try_on_runtime_wiring.py tests/test_try_on_sandbox_lifecycle.py tests/test_provider_runtime.py tests/test_status_routes_health_runtime.py tests/test_runtime_dependencies_container.py -q
```

Expected: PASS

- [ ] **Step 4: Run smoke verification**

Run:

```bash
python scripts/platform_foundation_smoke.py
```

Expected output still includes:

```text
operations_queue_backend=in_memory|redis
operations_worker_name=portable-worker
```

- [ ] **Step 5: Commit**

```bash
git add README.md docs/project_description.md docs/project_structure.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "docs: align fitfabrica agent system stage"
```

## Stage Exit Criteria

This stage is complete only when:

- `src/adk_agents` reflects approved FitFabrica product-agent roles
- support-only memory agents remain isolated from product-agent topology
- `primary_agent` and temporary agent folders are no longer active architecture
- Wave 1 Try-On agents are wired into backend-owned workflow boundaries
- later product agents use typed contracts and do not own orchestration

## Self-Review

Spec coverage checked:

- target `src/adk_agents` structure: covered by Topology and Tasks 1, 3, 5, 6, 7
- retained infrastructure-only support agents: covered by Topology and Task 5
- removed or archived legacy agents: covered by Topology and Task 5
- product-agent contracts for all approved roles: covered by Contract Package and Tasks 2, 6, 7
- execution order by business priority: covered by Execution Priority
- backend orchestration boundaries: covered by Architecture Rules and Tasks 4, 5

Placeholder scan checked:

- No `TODO`, `TBD`, or unresolved role placeholders remain.
- Every implementation-bearing task names concrete files and verification commands.

Type consistency checked:

- product-agent naming stays aligned with approved role names
- Wave 1 / 2 / 3 sequence matches backend workflow readiness
- support-only memory agents remain clearly separated from product-agent packages

## Current Implementation Status

Implemented in this worktree:

- Wave 1 product agents:
  - `human_identity_agent`
  - `garment_identity_agent`
  - `material_texture_agent`
  - `try_on_agent`
  - `quality_verifier_agent`
  - `repair_agent`
  - `fashion_stylist_agent`
- Wave 2 product agents:
  - `orchestrator_agent`
  - `user_profile_agent`
  - `business_profile_agent`
- Wave 3 product agents:
  - `marketplace_agent`
  - `trend_agent`
  - `pricing_agent`
  - `product_card_agent`
  - `cost_credits_agent`

Implemented guardrails and runtime status:

- `fitfabrica_agent_runtime_dependencies(...)` exposes the approved product-agent runtime bundle.
- product-agent packages are guarded against direct cross-import orchestration.
- `daily_memory_agent_tmp20260425_024853` is no longer part of the active runtime surface.
- `src/adk_agents/primary_agent` has been removed from the active ADK surface.
- `dialog_reply_task` is now the canonical backend reply-task name.
- `src/runtime_agents/dialog_reply` is now the canonical backend reply-runtime contour.
- legacy reply-task compatibility has been removed; the active runtime uses only `src/runtime_agents/dialog_reply` and `dialog_reply_task`.

Stage 11 is complete for the active architecture baseline. The remaining legacy surface is now a compatibility-only alias contour rather than an active architecture path.

Recommended next step after Stage 11:

- select the first portable backend deployment target
- execute portable staging rollout
- connect Firebase-hosted frontend surfaces to the portable backend API contour
