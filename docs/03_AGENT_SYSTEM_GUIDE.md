# AI FitFabrica - Agent System Guide

Дата актуализации: 2026-06-17

## 1. Главный принцип

Агенты не управляют продуктом. Backend управляет продуктом.

Агент:

- получает approved input от backend;
- возвращает structured JSON;
- указывает confidence, limitations, risks;
- не пишет в БД;
- не списывает credits;
- не вызывает других агентов напрямую;
- не принимает финальные business decisions.

Backend:

- выбирает workflow;
- вызывает нужных агентов через `AgentInvocationService`;
- валидирует contract;
- применяет policies;
- сохраняет результат;
- решает retry/repair/reject/success;
- списывает credits.

## 2. Где хранятся агенты

```text
src/adk_agents/<agent_name>/
├── agent.py
├── contracts.py
├── deploy_config.py
└── prompt_config.py
```

Что где менять:

- Prompt/instruction: `prompt_config.py`
- Prompt version / contract version: `prompt_config.py`
- Request/output schema: `contracts.py`
- Agent root wrapper: `agent.py`
- Default deploy/model config: `deploy_config.py`

Backend вызывает production agents через:

```text
src/use_cases/agents/invocation_service.py
src/adapters/agents/*
src/domain/agent_runtime.py
```

## 3. Canonical invocation flow

```text
Workflow use case
-> workflow-specific adapter
-> AgentInvocationService
-> AgentInvocationPort / gateway
-> provider runtime
-> strict contract validation
-> backend policy
-> persistence / workflow decision
```

Example Human Identity:

```text
Try-On workflow
-> HumanIdentityAnalysisAdapter
-> AgentInvocationService
-> ADK/Gemini gateway
-> HumanIdentityContract v2
-> HumanIdentityContinuationPolicy
-> persisted TryOnHumanIdentityAnalysis
```

## 4. Agent interaction model

Agents do not call each other directly.

Correct:

```text
Backend calls Human Identity Agent
Backend saves human analysis
Backend calls Garment Identity Agent
Backend saves garment analysis
Backend calls Try-On Instruction Agent with saved structured facts
Backend calls generation provider
Backend calls Quality Verifier
Backend decides repair/retry/success
```

Incorrect:

```text
Human Identity Agent -> Garment Identity Agent -> Try-On Agent
```

Direct A2A is not approved for current implementation.

## 5. Current agent list

| Agent | Responsibility | Current status | Suggested model tier |
| --- | --- | --- | --- |
| Orchestrator Agent | Suggest workflow intent to backend, never execute directly | planned | cheap text/reasoning model |
| User Profile Agent | Summarize/update B2C style, sizes, budget, preferences | planned/backend-service first | cheap text model or backend-only |
| Business Profile Agent | Seller profile, brand style, marketplace preferences | planned/backend-service first | cheap text model or backend-only |
| Human Identity Agent | Analyze human photo: face visibility, body coverage, subject count, pose, preservation constraints | production baseline accepted | Gemini Flash vision tier |
| Garment Identity Agent | Analyze clothing: count, target ambiguity, crop/coverage, occlusion, type, color, cut, collar, sleeves, buttons, pockets, print/logo, texture | local contract/policy hardening done; live acceptance pending | Gemini Flash vision tier, upgrade on ambiguity |
| Material / Texture Agent | Visual material estimate with honesty rules and evidence-backed signals | local contract/policy hardening done; live acceptance pending | Gemini Flash vision tier |
| Try-On Agent | Build evidence-backed generation instruction from saved analyses only | local contract/policy hardening done; live acceptance pending | Gemini Flash text/reasoning tier |
| Product Card Agent | Generate B2B product card content from saved garment analysis | wired for Product Card | Gemini Flash or Flash-Lite for text-only |
| Fashion Stylist Agent | Fit/style/color/outfit advice | planned/partial | Gemini Flash text tier |
| Marketplace Agent | Prepare legal marketplace search and compare approved results | planned | Flash + connector/search cost; no hidden scraping |
| Trend Agent | Convert trend signals into recommendations | planned | Flash with approved timestamped sources/search |
| Pricing Agent | Explain price positioning after backend comparable calculations | planned/partial | Gemini Flash text/reasoning tier |
| Quality Verifier Agent | Check result quality before user sees it | AgentInvocationService adapter integrated; selected wear-control live acceptance passed | strong vision model; Flash vision baseline, upgrade for critical QA |
| Repair Agent | Decide local repair instruction for fixable defects | AgentInvocationService planner integrated before image edit; fail-closed unsafe repair guard active | Flash vision for instruction, image model for edit |
| Cost / Credits Agent | Explain backend-calculated cost/credits to user/admin | planned | cheap text model or backend-only explanation |

## 6. Model routing baseline

Do not hardcode models in workflows. Current backend baseline lives in `src/llm/agent_model_routing.py` and is selected by:

```text
agent_name + task_kind + risk_tier
-> provider
-> model
-> fallback_model
-> max_cost_tier
```

Explicit `*_PREFERRED_MODEL` environment settings remain supported as controlled overrides.

2026-07-01 runtime update:

- `gemini_structured` is now the canonical Gemini runtime for both structured reasoning and agent invocations.
- The same `GeminiStructuredProvider` is wired as `structured_reasoning` and `agent_runtime`.
- `supports_artifacts=True` is required for vision agents such as Human Identity, Garment Identity, Material / Texture, Quality Verifier, and Repair Planner.
- Staging must use `LLM_PROVIDER=gemini_structured`, `VERTEX_PROJECT=ai-fitfabrica`, and an explicit `VERTEX_LOCATION` for live garment-photo workflows.
- `fake` remains valid only for local tests and sandbox flows; it cannot inspect uploaded image artifacts.

Current tiers:

### Cheap text tier

Use for:

- User Profile Agent;
- Business Profile Agent;
- Cost / Credits Agent explanations;
- Product Card text-only drafts when input facts are already structured;
- simple routing/orchestration suggestions.

Goal: reduce token cost for simple structured JSON tasks.

Current baseline model: `gemini-2.5-flash-lite`.

### Standard multimodal vision tier

Use for:

- Human Identity Agent;
- Garment Identity Agent;
- Material / Texture Agent;
- Quality Verifier baseline.

Goal: reliable image understanding without paying for the strongest model on every call.

Current baseline model: `gemini-2.5-flash`.

### Strong vision / critical QA tier

Use for:

- Quality Verifier on user-visible generated results;
- ambiguous garment/human cases;
- pre-publication B2B generated visuals;
- final approval gates where false pass is expensive.

Goal: reduce bad outputs shown to users.

Current baseline model: `gemini-2.5-flash`; upgrade only after measured false-pass/false-reject evidence.

### Image generation/editing tier

Use for:

- Try-On image generation;
- model photo generation;
- repair image generation / image edit;
- Content Package generated images.

Google image models such as Nano Banana / Gemini image generation-editing should be connected only through backend image generation/editing adapters. They should not be called from agents directly and never from frontend.

## 7. Per-agent model recommendation

| Agent/task | Recommended default | Fallback / upgrade | Notes |
| --- | --- | --- | --- |
| Human Identity | `gemini-2.5-flash` | stronger vision on low confidence | Already accepted baseline; keep cost controlled. |
| Garment Identity | `gemini-2.5-flash` | stronger vision for complex garment/logo/print | Live acceptance passed after multi-garment policy hardening. |
| Material / Texture | `gemini-2.5-flash` | stronger vision only for low confidence | Honesty policy should block exact composition claims without evidence. |
| Try-On Instruction | `gemini-2.5-flash` | stronger reasoning only if invalid instructions repeat | No source image access; backend blocks unsafe preservation/exclusion gaps. |
| Product Card text | `gemini-2.5-flash-lite` | Flash if channel rules complex | Structured garment analysis is already available. |
| Quality Verifier | `gemini-2.5-flash` | stronger vision for final production gate | Selected wear-control live acceptance passed. |
| Repair instruction | `gemini-2.5-flash` | stronger vision if defect localization is poor | Planner is integrated before image edit and fail-closed. |
| Repair image edit | Nano Banana / image editing provider | configured fallback image provider | Expensive generation/edit step; provider call is blocked for unsafe repair. |
| Fashion Stylist | `gemini-2.5-flash-lite` | Flash with search if trend-aware | Mostly text reasoning. |
| Marketplace | Flash text + connector | external connector/search provider | Connector cost must be separate. |
| Pricing | `gemini-2.5-flash-lite` | backend-only calculation + explanation | Backend calculates; agent explains. |
| Trend | Flash + approved source/search | stronger model only for synthesis | Needs timestamped source data. |
| Cost/Credits | backend-only or `gemini-2.5-flash-lite` | none | Backend must calculate exact cost. |

## 8. Agent acceptance process

Every agent must pass:

1. Contract test.
2. Prompt policy test.
3. Adapter test.
4. Backend policy/fail-closed test.
5. Golden/acceptance dataset.
6. Staging live run if it calls real provider.
7. Cost metadata check.
8. Docs update.

## 9. Human Identity status

Production baseline: accepted.

Acceptance result:

- `good_front.jpg` allowed.
- `side_pose.jpg` allowed.
- `blurry_dark.jpg` blocked.
- `cropped_face_only.jpg` blocked.
- `face_hidden.jpg` blocked.
- `multiple_people.jpg` blocked with `multiple_subjects_detected`.
- `multiple_people_masks.jpg` blocked with `multiple_subjects_detected`.
- `not_human.jpg` blocked with `no_human_subject_detected`.

Residual risks:

- Need larger dataset.
- Need rate-limit/backoff/circuit breaker for provider `429`.
- `preservation_targets` quality can be improved but is not a hard blocker.

## 10. Garment Identity status

Local backend hardening: completed.

Implemented locally:

- `garment_identity.contract.v2`;
- `GarmentIdentityContinuationPolicy`;
- explicit blocking for no garment, ambiguous multiple garments, insufficient crop/coverage, high occlusion, low confidence and high uncertainty;
- Product Card and Try-On adapters both use the same backend policy;
- local tests cover false-pass scenarios without provider calls.

Live acceptance status: pending VM/staging provider run.

## 11. Next live agent step: Garment Identity

Garment Identity must identify:

- garment type;
- primary/secondary colors;
- cut/silhouette;
- collar/neckline;
- sleeves;
- buttons/zippers;
- pockets;
- print/logo/pattern;
- visible texture/material cues;
- ambiguity and confidence.

Acceptance dataset should include:

- simple shirt;
- coat/jacket;
- dress;
- pants/jeans;
- patterned item;
- logo/print item;
- dark/blurry garment;
- cropped garment;
- multiple garments in frame;
- non-garment image.

Policy should block/request better input when:

- no garment detected;
- multiple ambiguous target garments;
- insufficient coverage;
- low confidence;
- source image cannot support required Product Card/Try-On facts.

## 11. Cost rules for agents

Agent invocation ledger stores:

- job_id;
- workflow_type;
- agent_name;
- provider/model;
- token/image counts;
- attempt/retry/repair reason;
- latency;
- validation status;
- estimated provider/internal cost;
- cost_config_version.

Failed pre-generation/system failures should not charge user credits. Provider/internal cost is still tracked for margin analysis.

## 12. Prompt writing rules

Prompts must:

- demand structured JSON;
- require confidence;
- require limitations;
- forbid invented facts;
- distinguish observed facts from assumptions;
- not ask agent to execute backend decisions;
- not include secrets or raw storage credentials;
- match `contracts.py`.

Prompts live in:

```text
src/adk_agents/<agent>/prompt_config.py
```
