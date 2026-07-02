# Multi-Garment Outfit Try-On Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Try-On from `human + one garment` to a backend-owned outfit mode that can accept upper, lower, outerwear, and full-body garment slots without breaking the existing single-item flow.

**Architecture:** Keep the current single-item Try-On as backward-compatible mode. Add typed garment slot roles in the domain/API, persist them as stored inputs, then add per-slot analysis and composition policy before enabling real multi-garment generation. Frontend remains thin: it uploads slot files and displays backend validation/status; backend owns slot validation, garment analysis, wear controls, generation instructions, quality checks, and billing.

**Tech Stack:** FastAPI, Pydantic, SQL-backed Try-On repository, existing object storage adapters, existing Garment Identity agent adapter, Next.js/React/TypeScript frontend.

---

## 1. Scope And Gates

This plan is intentionally split into gates.

- Gate A: API and persistence accept garment slots while preserving current `garment_photo`.
- Gate B: Garment Identity analyzes every uploaded garment slot independently.
- Gate C: Outfit Composition Policy validates slot compatibility and blocks impossible combinations.
- Gate D: Try-On Instruction includes normalized outfit slot facts and selected wear controls.
- Gate E: Frontend exposes an outfit upload UI with simple modes: one item, upper+lower, upper+lower+outerwear, full-body.
- Gate F: Quality Verifier checks the whole outfit and each slot.
- Gate G: Real provider live smoke confirms whether the selected generation backend supports multi-garment input quality.

Do not enable real paid multi-garment generation until Gates A-F pass locally and Gate G is approved for one paid smoke.

## 2. File Map

Backend domain/API:

- Modify `src/domain/try_on.py`: add `TryOnGarmentSlot` and extend upload roles.
- Modify `src/use_cases/try_on/workflow_upload_validation.py`: validate human plus at least one garment slot.
- Modify `src/use_cases/try_on/workflow_service.py`: accept optional slot uploads and persist them as separate inputs.
- Modify `src/entrypoints/try_on_routes.py`: accept `upper_garment_photo`, `lower_garment_photo`, `outerwear_garment_photo`, `full_body_garment_photo` while keeping `garment_photo`.
- Modify `apps/web/src/lib/api/contracts.ts`: expose slot metadata roles.

Backend analysis:

- Modify `src/adapters/agents/try_on_garment_identity_analysis.py`: initially choose the primary garment for backward-compatible analysis; later return per-slot bundle.
- Create `src/domain/try_on_outfit.py`: outfit slot analysis and composition verdict models.
- Create `src/use_cases/try_on/outfit_composition_policy.py`: deterministic slot compatibility rules.

Frontend:

- Modify `apps/web/src/features/workspace/try-on-workflow.tsx`: add upload mode selector and slot uploads.
- Create `apps/web/src/features/workspace/try-on-garment-slot-upload.tsx`: reusable slot upload card.

Tests:

- Create `tests/test_try_on_multi_garment_upload_contract.py`.
- Create `tests/test_try_on_outfit_composition_policy.py`.
- Update `tests/test_try_on_sandbox_lifecycle.py`.
- Update `tests/test_workspace_try_on_page.py` or create `tests/test_workspace_try_on_multi_garment_page.py`.

## 3. Task 1: Backward-Compatible Multi-Garment Upload Contract

**Files:**
- Modify: `src/domain/try_on.py`
- Modify: `src/use_cases/try_on/workflow_upload_validation.py`
- Modify: `src/use_cases/try_on/workflow_service.py`
- Modify: `src/entrypoints/try_on_routes.py`
- Test: `tests/test_try_on_multi_garment_upload_contract.py`

- [ ] **Step 1: Write failing tests**

Test cases:

```python
def test_try_on_upload_roles_include_outfit_slots() -> None:
    assert TryOnUploadRole.UPPER_GARMENT_PHOTO.value == "upper_garment_photo"
    assert TryOnUploadRole.LOWER_GARMENT_PHOTO.value == "lower_garment_photo"
    assert TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO.value == "outerwear_garment_photo"
    assert TryOnUploadRole.FULL_BODY_GARMENT_PHOTO.value == "full_body_garment_photo"
```

```python
def test_missing_fields_accepts_legacy_single_garment() -> None:
    assert missing_fields(human_photo=object(), garment_photo=object()) == []
```

```python
def test_missing_fields_requires_at_least_one_garment_slot() -> None:
    assert "garment_photo" in missing_fields(human_photo=object(), garment_photo=None)
```

```python
def test_missing_fields_accepts_upper_and_lower_slots() -> None:
    assert missing_fields(
        human_photo=object(),
        garment_photo=None,
        upper_garment_photo=object(),
        lower_garment_photo=object(),
    ) == []
```

- [ ] **Step 2: Run RED**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_try_on_multi_garment_upload_contract.py -q
```

Expected: fails because new roles and function arguments do not exist.

- [ ] **Step 3: Implement roles and upload validation**

Add roles:

```python
UPPER_GARMENT_PHOTO = "upper_garment_photo"
LOWER_GARMENT_PHOTO = "lower_garment_photo"
OUTERWEAR_GARMENT_PHOTO = "outerwear_garment_photo"
FULL_BODY_GARMENT_PHOTO = "full_body_garment_photo"
```

Update validation to require:

- `human_photo` is present;
- at least one of `garment_photo`, `upper_garment_photo`, `lower_garment_photo`, `outerwear_garment_photo`, `full_body_garment_photo` is present.

- [ ] **Step 4: Implement workflow service slot persistence**

Extend `TryOnWorkflowService.create_job(...)` with optional slot uploads. Persist every provided slot using the matching `TryOnUploadRole`.

- [ ] **Step 5: Implement route fields**

Extend `POST /api/try-on/jobs` with optional slot file fields and pass them to workflow service.

- [ ] **Step 6: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_try_on_multi_garment_upload_contract.py tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: all pass.

## 4. Task 2: Primary Garment Compatibility Adapter

**Files:**
- Modify: `src/adapters/agents/try_on_garment_identity_analysis.py`
- Test: `tests/test_try_on_multi_garment_upload_contract.py`

- [ ] **Step 1: Write failing test**

Verify that Garment Identity chooses `garment_photo` first for legacy jobs, otherwise chooses the first slot in this order:

```text
full_body_garment_photo -> upper_garment_photo -> lower_garment_photo -> outerwear_garment_photo
```

- [ ] **Step 2: Implement primary garment selector**

Add a small helper in the adapter. Do not yet pretend full multi-garment analysis is complete.

- [ ] **Step 3: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_try_on_multi_garment_upload_contract.py tests/test_try_on_garment_material_analysis_adapters.py -q
```

Expected: all pass.

## 5. Task 3: Frontend Upload Modes

**Files:**
- Modify: `apps/web/src/lib/api/contracts.ts`
- Modify: `apps/web/src/features/workspace/try-on-workflow.tsx`
- Create: `apps/web/src/features/workspace/try-on-garment-slot-upload.tsx`
- Test: `tests/test_workspace_try_on_multi_garment_page.py`

- [ ] **Step 1: Write failing frontend guardrail test**

Assert the Try-On UI contains:

- `single_item`;
- `upper_lower`;
- `upper_lower_outerwear`;
- `full_body`;
- `upper_garment_photo`;
- `lower_garment_photo`;
- `outerwear_garment_photo`;
- `full_body_garment_photo`.

- [ ] **Step 2: Implement UI mode selector**

Modes:

- `single_item`: old one-garment flow;
- `upper_lower`: upper and lower required;
- `upper_lower_outerwear`: upper and lower required, outerwear optional;
- `full_body`: full-body item required.

- [ ] **Step 3: Submit correct form fields**

Append only files required by the selected mode. Do not send empty file fields.

- [ ] **Step 4: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_workspace_try_on_multi_garment_page.py -q
npm run lint
npm run typecheck
npm run build
```

Expected: all pass.

## 6. Task 4: Outfit Composition Policy

**Files:**
- Create: `src/domain/try_on_outfit.py`
- Create: `src/use_cases/try_on/outfit_composition_policy.py`
- Test: `tests/test_try_on_outfit_composition_policy.py`

- [ ] **Step 1: Write failing policy tests**

Required behavior:

- full-body cannot be combined with upper/lower in v1;
- lower without upper is allowed only for single lower-item try-on mode if explicitly selected later;
- upper+lower is valid;
- upper+lower+outerwear is valid;
- duplicate same slot is invalid.

- [ ] **Step 2: Implement deterministic policy**

Return structured verdict:

```python
decision: "allow" | "block" | "request_better_input"
reasons: list[str]
warnings: list[str]
```

- [ ] **Step 3: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_try_on_outfit_composition_policy.py -q
```

Expected: all pass.

## 7. Final Verification For This Plan Slice

Run:

```powershell
.venv\Scripts\python.exe scripts/check_architecture.py
.venv\Scripts\python.exe -m compileall -q src
.venv\Scripts\python.exe -m pytest tests/test_try_on_multi_garment_upload_contract.py tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_garment_material_analysis_adapters.py tests/test_workspace_try_on_multi_garment_page.py tests/test_try_on_outfit_composition_policy.py -q
npm run lint
npm run typecheck
npm run build
```

Expected:

- architecture passed;
- compileall passed;
- targeted backend tests passed;
- frontend lint/typecheck/build passed.

## 8. Rollback Plan

If multi-garment upload causes issues:

- keep frontend on `single_item` mode only;
- backend continues accepting legacy `garment_photo`;
- ignore new slot fields in client deploy;
- do not enable multi-garment real provider smoke;
- no data migration rollback is needed because slots are stored as existing `TryOnStoredInput.role` values.
