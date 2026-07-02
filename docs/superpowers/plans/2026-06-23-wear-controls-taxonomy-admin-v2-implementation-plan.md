# Wear Controls, Taxonomy Admin and Agent Acceptance v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the original agent rollout roadmap while adding the new Garment Wear Controls and admin taxonomy review layer exactly where it belongs: after Garment Identity understanding and before Try-On instruction, quality verification and repair.

**Architecture:** Backend remains the orchestrator. Agents return structured JSON only; backend validates, persists, gates, exposes UI state and records audit decisions. New taxonomy learning is semi-automatic: AI proposes candidates, a human approves through admin review, backend applies approved rules.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, PostgreSQL, Redis worker runtime, Next.js/React/TypeScript, Google Gen AI/Gemini through existing provider-neutral adapters.

---

## 0. Plan Review Verdict

The previous plan was directionally correct but had five weak points:

- It could be misunderstood as replacing the old roadmap. It must not. `Garment Identity live acceptance` remains first.
- It placed `/admin/taxonomy` too close to the beginning. Admin UI must come after backend candidate capture exists.
- It did not explicitly require admin auth, feature flag and audit log before any admin mutation endpoint is exposed.
- It did not define rollback and fail-closed behavior for taxonomy mistakes.
- It did not separate live-acceptance work, which needs VM, from local domain/contracts/tests work, which does not.

This v2 plan fixes those gaps.

## 1. Final Integrated Roadmap

1. Finish `Garment Identity Agent live acceptance`.
2. Add backend taxonomy and wear-control foundation.
3. Add taxonomy candidate capture with human approval status, no automatic production mutation.
4. Extend Garment Identity output mapping to taxonomy and wear controls.
5. Extend Try-On job options with selected wear control.
6. Integrate selected wear control into Try-On Instruction.
7. Extend Quality Verifier policy with wear-control match checks.
8. Add Repair actions for safe local wear-control corrections.
9. Add `/admin/taxonomy` after backend candidate flow and admin guard exist.
10. Continue Material / Texture, model routing, marketplace/search and recalibration according to the broader roadmap.

## 2. VM Decision

VM is required for Task 1 only: `Garment Identity live acceptance`, because it calls the real Gemini/agent runtime on staging assets.

VM is not required for Tasks 2-9 while writing local domain models, migrations, repository tests, API contracts and frontend/admin UI tests.

Recommendation before implementation:

- If we start with Task 1 now: keep VM on.
- If we postpone live acceptance and only implement local code foundations: turn VM off.
- Since the correct next roadmap step is Task 1, keep VM on for the next working block.

## 3. Non-Negotiable Rules

- No new `Wear Control Agent`.
- No direct frontend AI/model calls.
- No automatic production taxonomy mutation from AI output.
- No public admin endpoints.
- No admin mutation without role check, feature flag and audit log.
- No free-form user prompt in v1.
- No wear-control generation requirement unless backend has validated the selected control.
- No clean `pass` if selected wear control is visibly violated.

## 4. Files and Responsibilities

### Existing files to extend

- `src/adk_agents/garment_identity_agent/contracts.py`: add taxonomy and wear-control candidate fields after acceptance confirms needed shape.
- `src/adk_agents/garment_identity_agent/prompt_config.py`: require taxonomy classification and wear-control candidate output.
- `src/domain/garment_identity.py`: backend policy-level garment identity verdict models stay focused on safety.
- `src/domain/try_on.py`: add selected wear-control state to Try-On aggregate only after backend taxonomy exists.
- `src/domain/try_on_instruction.py`: include selected wear-control facts in instruction models.
- `src/use_cases/try_on/instruction_policy.py`: block missing/opposite wear-control instructions when selected.
- `src/use_cases/try_on/quality_policy.py`: unsafe pass override for wear-control failure.
- `src/use_cases/try_on/repair_policy.py`: allow only safe local wear-control repair actions.
- `src/entrypoints/try_on_routes.py`: accept selected wear control after typed contract is ready.
- `apps/web/src/features/workspace/try-on-workflow.tsx`: show only backend-provided allowed controls.
- `apps/web/src/features/workspace/try-on-result.tsx`: later show repair actions only from backend.

### New backend files

- `src/domain/garment_taxonomy.py`: taxonomy item, wear control, candidate, review status and audit models.
- `src/use_cases/garment_taxonomy/catalog_policy.py`: validate allowed control, safe fallback and candidate creation decisions.
- `src/use_cases/garment_taxonomy/ports.py`: repository protocols.
- `src/use_cases/garment_taxonomy/service.py`: catalog read, candidate capture, admin review orchestration.
- `src/adapters/database/sql/garment_taxonomy_models.py`: SQLAlchemy tables.
- `src/adapters/database/sql/garment_taxonomy_repositories.py`: SQL repository implementation.
- `src/entrypoints/garment_taxonomy_routes.py`: read-only catalog endpoints for workspace/admin.
- `src/entrypoints/admin_taxonomy_routes.py`: admin-only review endpoints behind feature flag.
- `alembic/versions/20260623_000017_garment_taxonomy.py`: migration.

### New frontend files

- `apps/web/src/features/workspace/garment-wear-control-picker.tsx`: user-facing control picker.
- `apps/web/src/app/(admin)/admin/taxonomy/page.tsx`: admin taxonomy review shell, disabled/locked unless backend capability allows.
- `apps/web/src/features/admin/taxonomy-review.tsx`: candidate list and review actions.
- `apps/web/src/lib/api/admin-contracts.ts`: typed admin DTOs.

### New tests

- `tests/test_garment_taxonomy_domain.py`
- `tests/test_garment_taxonomy_sql_migration.py`
- `tests/test_garment_taxonomy_service.py`
- `tests/test_garment_identity_wear_controls_contract.py`
- `tests/test_try_on_wear_control_options.py`
- `tests/test_try_on_instruction_wear_controls.py`
- `tests/test_try_on_quality_wear_controls.py`
- `tests/test_try_on_repair_wear_controls.py`
- `tests/test_admin_taxonomy_routes.py`
- `tests/test_admin_taxonomy_page.py`

## 5. Task 1: Garment Identity Live Acceptance

**Files:**

- Use existing: `scripts/garment_identity_live_acceptance.py`
- Use existing: `tests/test_garment_identity_live_acceptance_script.py`
- Update after run: `docs/01_ACTION_LOG_CHECKLIST.md`

- [ ] **Step 1: Confirm VM health**

Run:

```powershell
python - <<'PY'
import json, urllib.request
with urllib.request.urlopen("https://api.fit.aisoulfabrica.com/health", timeout=30) as r:
    data = json.loads(r.read().decode("utf-8"))
    print(r.status, data["try_on_real_activation"]["backend"], data["operations"]["queue_depth"])
PY
```

Expected: `200`, backend can remain `sandbox_fake`, queue depth `0`.

- [ ] **Step 2: Confirm garment dataset is present on VM**

Run VM check:

```powershell
gcloud compute ssh ubuntu@fitfabrica-staging-vm --zone=europe-west1-b --command="find /opt/fitfabrica/test-assets/garment-identity -maxdepth 1 -type f | sort"
```

Expected cases:

```text
simple_shirt
coat_or_jacket
dress
pants_or_jeans
patterned_item
logo_or_print_item
dark_or_blurry_garment
cropped_garment
multiple_garments
not_garment
```

- [ ] **Step 3: Run live acceptance**

Run the existing live script on VM using the configured provider env.

Expected report must include:

```text
expected_decision
actual_decision
garment_type
dominant_color
silhouette_summary
preserved_details
policy_decision
rejection_reasons
```

- [ ] **Step 4: Gate decision**

Pass criteria:

- `0` critical false pass for no-garment, cropped/insufficient, ambiguous multiple garments.
- Good garments have useful type/color/detail output.
- Bad inputs are blocked before generation.

If failed:

- Do not start Wear Controls implementation.
- Harden Garment Identity prompt/policy first.

## 6. Task 2: Taxonomy Domain and Migration

**Files:**

- Create: `src/domain/garment_taxonomy.py`
- Create: `alembic/versions/20260623_000017_garment_taxonomy.py`
- Test: `tests/test_garment_taxonomy_domain.py`
- Test: `tests/test_garment_taxonomy_sql_migration.py`

- [ ] **Step 1: Write failing domain tests**

Required behaviors:

- taxonomy item code is stable and lowercase;
- wear control belongs to a taxonomy item or parent category;
- candidate status starts as `pending_review`;
- approved candidate cannot mutate catalog without admin actor id;
- rejected candidate records reason.

- [ ] **Step 2: Implement domain models**

Model names:

```python
GarmentTaxonomyItem
GarmentWearControl
GarmentTaxonomyCandidate
GarmentTaxonomyAuditEvent
GarmentTaxonomyCandidateStatus
GarmentWearControlRiskLevel
```

- [ ] **Step 3: Write failing migration test**

Migration must contain:

```text
garment_taxonomy_items
garment_wear_controls
garment_taxonomy_candidates
garment_taxonomy_audit_log
```

- [ ] **Step 4: Implement migration**

Use JSON columns for proposed controls and before/after audit snapshots.

- [ ] **Step 5: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_garment_taxonomy_domain.py tests/test_garment_taxonomy_sql_migration.py -q
```

Expected: all pass.

## 7. Task 3: Taxonomy Service and Candidate Capture

**Files:**

- Create: `src/use_cases/garment_taxonomy/ports.py`
- Create: `src/use_cases/garment_taxonomy/catalog_policy.py`
- Create: `src/use_cases/garment_taxonomy/service.py`
- Create: `src/adapters/database/sql/garment_taxonomy_models.py`
- Create: `src/adapters/database/sql/garment_taxonomy_repositories.py`
- Test: `tests/test_garment_taxonomy_service.py`

- [ ] **Step 1: Write failing service tests**

Required behaviors:

- known garment type returns allowed controls;
- unknown garment type creates candidate;
- unknown control is dropped;
- `auto` resolves to recommended backend choice;
- production catalog is not changed by candidate creation.

- [ ] **Step 2: Implement repository ports**

Required methods:

```python
get_item_by_code(code)
list_controls_for_item_or_parent(code)
save_candidate(candidate)
list_candidates(status)
review_candidate(candidate_id, decision, actor_id)
write_audit_event(event)
```

- [ ] **Step 3: Implement service**

Service must be backend-only and deterministic.

- [ ] **Step 4: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_garment_taxonomy_service.py -q
```

Expected: all pass.

## 8. Task 4: Garment Identity Contract Extension

**Files:**

- Modify: `src/adk_agents/garment_identity_agent/contracts.py`
- Modify: `src/adk_agents/garment_identity_agent/prompt_config.py`
- Modify: `src/adapters/agents/try_on_garment_identity_analysis.py`
- Modify: `src/adapters/agents/garment_identity_analysis.py`
- Test: `tests/test_garment_identity_wear_controls_contract.py`

- [ ] **Step 1: Write failing contract tests**

Required fields:

```text
taxonomy_parent
taxonomy_confidence
wear_control_candidates
unknown_taxonomy_candidate
```

- [ ] **Step 2: Implement contract fields**

Do not remove existing v2 fields.

- [ ] **Step 3: Update prompt**

Prompt must say:

```text
Return only controls that are visually supported.
If garment type is unknown, provide unknown_taxonomy_candidate instead of inventing production rules.
```

- [ ] **Step 4: Adapter mapping**

Adapters must call taxonomy service to validate and normalize agent output.

- [ ] **Step 5: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_garment_identity_wear_controls_contract.py tests/test_product_card_garment_identity_adapter.py tests/test_try_on_garment_material_analysis_adapters.py -q
```

Expected: all pass.

## 9. Task 5: Try-On Options and Frontend Picker

**Files:**

- Modify: `src/domain/try_on.py`
- Modify: `src/entrypoints/try_on_routes.py`
- Modify: `apps/web/src/lib/api/contracts.ts`
- Create: `apps/web/src/features/workspace/garment-wear-control-picker.tsx`
- Modify: `apps/web/src/features/workspace/try-on-workflow.tsx`
- Test: `tests/test_try_on_wear_control_options.py`
- Test: `tests/test_workspace_try_on_wear_controls_page.py`

- [ ] **Step 1: Write failing backend tests**

Required behaviors:

- missing selected control means `auto`;
- invalid selected control returns typed validation error;
- selected control is persisted on job.

- [ ] **Step 2: Implement backend DTO and persistence**

Only accept backend-known control codes.

- [ ] **Step 3: Write failing frontend tests**

Required UI states:

- loading;
- disabled until garment analysis/capability allows;
- only backend-provided options visible;
- no free-form prompt input.

- [ ] **Step 4: Implement picker**

User-facing labels must be Russian, API values remain stable English codes.

- [ ] **Step 5: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_try_on_wear_control_options.py -q
npm run lint
npm run typecheck
```

Expected: all pass.

## 10. Task 6: Try-On Instruction, Quality and Repair Gates

**Files:**

- Modify: `src/adk_agents/try_on_agent/contracts.py`
- Modify: `src/adk_agents/try_on_agent/prompt_config.py`
- Modify: `src/use_cases/try_on/instruction_policy.py`
- Modify: `src/adk_agents/quality_verifier_agent/contracts.py`
- Modify: `src/use_cases/try_on/quality_policy.py`
- Modify: `src/use_cases/try_on/repair_policy.py`
- Test: `tests/test_try_on_instruction_wear_controls.py`
- Test: `tests/test_try_on_quality_wear_controls.py`
- Test: `tests/test_try_on_repair_wear_controls.py`

- [ ] **Step 1: Write failing instruction tests**

Required behavior:

- selected `untucked` must appear in instruction;
- opposite instruction `tucked into waistband` is blocked;
- confidence below threshold blocks generation.

- [ ] **Step 2: Implement instruction fields and policy**

Do not pass raw UI text. Pass normalized backend control object.

- [ ] **Step 3: Write failing quality tests**

Required behavior:

- quality `pass` with violated wear control is overridden to warning/fail;
- repairable local wear-control defect routes to repair;
- non-local defect routes to retry/reject.

- [ ] **Step 4: Implement quality and repair policies**

No image-editing provider call for unsafe repair.

- [ ] **Step 5: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_try_on_instruction_wear_controls.py tests/test_try_on_quality_wear_controls.py tests/test_try_on_repair_wear_controls.py -q
```

Expected: all pass.

## 11. Task 7: Admin Taxonomy Backend

**Files:**

- Create: `src/entrypoints/admin_taxonomy_routes.py`
- Modify: `src/entrypoints/http_routes.py`
- Modify: `src/settings_model_app.py`
- Test: `tests/test_admin_taxonomy_routes.py`

- [ ] **Step 1: Write failing route tests**

Required behavior:

- routes are disabled unless `ENABLE_ADMIN_TAXONOMY=true`;
- missing admin role returns `403`;
- approve writes audit log;
- reject writes audit log;
- merge requires existing target code.

- [ ] **Step 2: Implement settings flag**

Setting:

```text
ENABLE_ADMIN_TAXONOMY=false
```

Default must be false.

- [ ] **Step 3: Implement routes**

Expose:

```text
GET /api/admin/taxonomy/candidates
POST /api/admin/taxonomy/candidates/{candidate_id}/approve
POST /api/admin/taxonomy/candidates/{candidate_id}/reject
POST /api/admin/taxonomy/candidates/{candidate_id}/merge
POST /api/admin/taxonomy/candidates/{candidate_id}/rename-and-approve
```

- [ ] **Step 4: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_admin_taxonomy_routes.py -q
```

Expected: all pass.

## 12. Task 8: Admin Taxonomy UI

**Files:**

- Create: `apps/web/src/app/(admin)/admin/taxonomy/page.tsx`
- Create: `apps/web/src/features/admin/taxonomy-review.tsx`
- Create: `apps/web/src/lib/api/admin-contracts.ts`
- Test: `tests/test_admin_taxonomy_page.py`

- [ ] **Step 1: Write failing page tests**

Required states:

- locked when backend says disabled;
- loading;
- empty candidates;
- error;
- candidate list;
- approve/reject/merge actions disabled during submit.

- [ ] **Step 2: Implement page shell**

No production mutation if backend capability is disabled.

- [ ] **Step 3: Verify frontend**

Run:

```powershell
npm run lint
npm run typecheck
npm run build
```

Expected: all pass.

## 13. Final Verification

Run before claiming complete:

```powershell
.venv\Scripts\python.exe scripts/check_architecture.py
.venv\Scripts\python.exe -m compileall -q src
.venv\Scripts\python.exe -m pytest -q
npm run lint
npm run typecheck
npm run build
```

Expected:

- architecture passed;
- compileall passed;
- pytest passed;
- frontend lint/typecheck/build passed.

## 14. Rollback Plan

If taxonomy/wear-control rollout causes issues:

- Disable admin routes with `ENABLE_ADMIN_TAXONOMY=false`.
- Default Try-On `selected_wear_control` to `auto`.
- Ignore agent-proposed unknown taxonomy candidates for user-facing generation.
- Keep production catalog read-only.
- Leave existing Try-On generation path unchanged.

## 15. Readiness Gates

Do not proceed to the next gate unless current gate passes:

- Gate A: Garment Identity live acceptance has `0` critical false pass.
- Gate B: taxonomy foundation works locally with tests.
- Gate C: Try-On selected control is persisted and validated.
- Gate D: instruction includes selected control.
- Gate E: quality cannot clean-pass violated control.
- Gate F: repair action is local and safe.
- Gate G: admin mutation requires feature flag, admin role and audit log.

## 16. Execution Choice

Recommended execution mode:

1. Finish Gate A with VM on.
2. Turn VM off.
3. Implement Gates B-G locally with tests.
4. Turn VM on again only for live acceptance after local verification.

