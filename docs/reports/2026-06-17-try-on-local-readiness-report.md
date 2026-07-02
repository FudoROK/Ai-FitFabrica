# Try-On Local Readiness Report - 2026-06-17

## Verdict

Local backend hardening for the Try-On agent chain is ready for staging/live acceptance.

VM is not required for more local development in this pass. VM/staging is required only for live provider calls, generated images, image edit checks, backend deploy smoke, and end-to-end acceptance.

## Local Chain Status

| Stage | Local status | Backend protection now in place | Live status |
| --- | --- | --- | --- |
| Human Identity | accepted baseline | blocks no-human, multi-person, hidden face, headshot crop, insufficient body coverage | live accepted on 8 assets |
| Garment Identity | ready locally | blocks no garment, ambiguous target, tight crop, insufficient garment coverage, high occlusion, low confidence, high uncertainty | pending |
| Material / Texture | ready locally | blocks empty material analysis, missing evidence, low confidence, high uncertainty, unsupported composition claims | pending |
| Try-On Instruction | ready locally | blocks disabled face/body/pose preservation, missing garment focus, missing exclusions, missing evidence, low confidence, high uncertainty | pending |
| Quality Verifier | ready locally | overrides unsafe pass when checks are missing, failed, warning-only, or confidence is too low | pending |
| Repair / Image Edit | ready locally | repairs only local warning-level defects; blocks failed/non-local repairs before image-edit provider call; second quality verification is required | pending |

## Local Verification Passed

Run group already passed locally:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_garment_identity_policy.py tests/test_material_texture_policy.py tests/test_try_on_instruction_policy.py tests/test_try_on_quality_policy.py tests/test_try_on_repair_policy.py
.venv\Scripts\python.exe scripts\check_architecture.py
.venv\Scripts\python.exe -m compileall -q src
```

Latest targeted checks completed during hardening:

- Garment Identity: `64 passed`
- Material / Texture: `58 passed`
- Try-On Instruction: `73 passed`
- Quality Verifier: `61 passed`
- Repair / Image Edit: `53 passed`
- Architecture check: passed
- Compileall: passed

## What VM Must Validate

### 1. Garment Identity live acceptance

Dataset:

- clean single shirt / top;
- coat or jacket;
- dress;
- pants / jeans;
- patterned item;
- logo or print item;
- dark or blurry garment;
- cropped garment;
- multiple garments in frame;
- non-garment image.

Expected:

- good single garment images allowed;
- no-garment blocked;
- ambiguous multiple garments blocked;
- tight crop blocked or request better input;
- insufficient coverage blocked before generation.

Command on VM:

```bash
cd /opt/fitfabrica
python3 scripts/garment_identity_live_acceptance.py \
  --assets-dir test-assets/garment-identity \
  --output output/garment_identity_live_acceptance_vm.jsonl
```

Strict gate command:

```bash
cd /opt/fitfabrica
.venv311/bin/python scripts/garment_identity_live_acceptance.py \
  --assets-dir test-assets/garment-identity \
  --output output/garment_identity_live_acceptance_vm.jsonl \
  --require-pass
```

Status as of 2026-06-19:

- Passed on VM `fitfabrica-staging-vm` after synchronizing the Garment Identity runtime to contract v2.
- Final command used `.venv311/bin/python` because the project requires Python 3.11+.
- Final result: `10/10 matched`, `false_pass_count=0`, `false_reject_count=0`.
- Final artifact: `output/garment_identity_live_acceptance_vm_v2.jsonl`.
- Initial stale-runtime run failed with two false passes: `cropped_garment.png` and `multiple_garments.png`; this was caused by old VM code still using contract v1.

### 2. Material / Texture live acceptance

Dataset:

- `matte_cotton_like.png` - clear matte cotton-like visual;
- `shiny_satin_like.png` - clear shiny satin/silk-like visual;
- `denim_texture.png` - visible denim weave/texture;
- `knit_texture.png` - visible knit/wool-like texture;
- `leather_like_finish.png` - leather-like or faux-leather visual finish;
- `sheer_transparent_fabric.png` - transparent or sheer item;
- `dark_or_blurry_fabric.png` - poor evidence, expected blocked;
- `no_material_evidence.png` - non-fabric or unusable material evidence, expected blocked.

Expected:

- visual texture/material cues are described as estimates;
- exact fiber composition is not claimed without trusted facts;
- poor evidence leads to low confidence/high uncertainty or block.

Command on VM:

```bash
cd /opt/fitfabrica
.venv311/bin/python scripts/material_texture_live_acceptance.py \
  --env-file .env.portable-remote-staging.local \
  --assets-dir test-assets/material-texture \
  --output output/material_texture_live_acceptance_vm.jsonl
```

Strict gate command:

```bash
cd /opt/fitfabrica
.venv311/bin/python scripts/material_texture_live_acceptance.py \
  --env-file .env.portable-remote-staging.local \
  --assets-dir test-assets/material-texture \
  --output output/material_texture_live_acceptance_vm.jsonl \
  --require-pass
```

Status as of 2026-06-20:

- Passed on VM `fitfabrica-staging-vm`.
- VM runtime checked: `material_texture.contract.v2`.
- VM targeted tests passed: `26 passed`.
- Final result: `8/8 matched`, `false_pass_count=0`, `false_reject_count=0`.
- Final artifact: `output/material_texture_live_acceptance_vm.jsonl`.

### 3. Try-On Instruction live acceptance

Input:

- approved Human Identity snapshot;
- approved Garment Identity snapshot;
- approved Material / Texture snapshot.

Expected:

- no source image access in instruction agent;
- preserve face/body/pose stays enabled;
- garment focus points present;
- generation exclusions present;
- evidence present;
- unsafe instruction blocked before image generation.

Status as of 2026-06-20:

- Passed on VM `fitfabrica-staging-vm`.
- VM runtime checked: `try_on.contract.v2`.
- Initial run failed with two false rejects because Gemini omitted `generation_exclusions`.
- Prompt was hardened to require non-empty `generation_exclusions` with explicit identity/body/pose/detail exclusions.
- VM targeted tests passed after hardening: `30 passed`.
- Final result: `2/2 matched`, `false_pass_count=0`, `false_reject_count=0`.
- Final artifact: `output/try_on_instruction_live_acceptance_vm_v2.jsonl`.

### 4. Quality Verifier live visual acceptance

Dataset:

Create `test-assets/quality-verifier/<case_name>/` folders. Each folder must contain:

- `human_source.png`;
- `garment_source.png`;
- `generated_result.png`.

Required cases:

- `good_generated_result` - expected `pass`;
- `minor_background_artifact` - expected `repair_recommended`;
- `minor_color_shift` - expected `repair_recommended`;
- `face_changed` - expected `reject`;
- `body_pose_changed` - expected `reject`;
- `wrong_garment` - expected `reject`;
- `missing_key_garment_detail` - expected `reject`;
- `severe_anatomy_artifact` - expected `reject`.

Expected:

- obvious broken results are not passed;
- local minor defects become `repair_recommended`;
- severe identity/body/garment failures become `reject`;
- low-confidence pass is downgraded by backend policy.

Status as of 2026-06-21:

- Passed on VM `fitfabrica-staging-vm`.
- VM runtime checked: `quality_verifier.contract.v2`.
- Initial run found two mismatches: `missing_key_garment_detail` and `severe_anatomy_artifact` were returned as `repair_recommended`.
- Prompt was hardened so missing key garment details and severe hand/finger/neck/waist/limb anatomy defects are blocking `reject` cases.
- VM targeted tests passed after hardening: `22 passed`.
- Final result: `8/8 matched`, `false_pass_count=0`, `false_repair_count=0`, `false_reject_count=0`.
- Final artifact: `output/quality_verifier_live_acceptance_vm_v2.jsonl`.

Command on VM:

```bash
cd /opt/fitfabrica
.venv311/bin/python scripts/quality_verifier_live_acceptance.py \
  --env-file .env.portable-remote-staging.local \
  --assets-dir test-assets/quality-verifier \
  --output output/quality_verifier_live_acceptance_vm.jsonl
```

Strict gate command:

```bash
cd /opt/fitfabrica
.venv311/bin/python scripts/quality_verifier_live_acceptance.py \
  --env-file .env.portable-remote-staging.local \
  --assets-dir test-assets/quality-verifier \
  --output output/quality_verifier_live_acceptance_vm.jsonl \
  --require-pass
```

### 5. Repair Agent live acceptance

Dataset:

- local background/color defects;
- non-local identity/body/pose failures;
- generated artifacts from the Quality Verifier acceptance dataset.

Expected:

- local warning-level defects are sent to repair;
- failed/non-local defects do not call image-edit provider;
- unsafe cases are blocked before image edit;
- backend receives a structured repair plan and scope.

Status:

- Done on 2026-06-21.
- VM script: `scripts/repair_agent_live_acceptance.py`.
- VM report: `output/repair_agent_live_acceptance_vm.jsonl`.
- Result: `4/4 matched`, `mismatch_count=0`, `false_local_count=0`, `false_unsafe_count=0`.

Important limitation:

- This validates the Repair Agent decision/plan/gating stage only.
- Real image-edit provider live smoke passed on 2026-06-21.
- Code wiring now supports `IMAGE_EDITING_PROVIDER=google_genai` behind `ImageEditingPort`.
- Repaired output received a second Quality Verifier pass in VM/staging repair workflow acceptance on 2026-06-21.

### 6. Real Image Edit provider acceptance

Expected:

- local repair plans call a real image-edit adapter;
- identity/body/pose failures never call image edit;
- repaired artifact is persisted;
- repaired result receives second Quality Verifier verification;
- user sees only final pass result.

Implementation status:

- Google GenAI image-editing adapter added on 2026-06-21.
- Runtime switch: `IMAGE_EDITING_PROVIDER=google_genai`.
- Required model env: `IMAGE_EDITING_MODEL`.
- Smoke CLI: `scripts/image_editing_live_smoke.py`.
- Local unit/contract tests passed.
- VM/staging smoke passed with `imagen-3.0-capability-001`.
- Live constraints discovered and fixed: output must be `image/png` or `image/jpeg`, and the Google image-edit call expects one raw image.
- Full repair workflow acceptance with second Quality Verifier passed on 2026-06-21.

## Required VM Preconditions

- Backend environment configured for staging provider calls.
- Google credentials and project config active.
- Provider quotas available.
- Test images uploaded or mounted in a known folder.
- Object storage available for generated and repaired artifacts.
- Logs enabled for agent invocation and workflow stages.

## Recommended Live Run Order

1. Garment Identity live acceptance. Done on 2026-06-19.
2. Material / Texture live acceptance. Done on 2026-06-20.
3. Try-On Instruction live acceptance with saved upstream snapshots. Done on 2026-06-20.
4. Quality Verifier live visual acceptance. Done on 2026-06-21.
5. Repair Agent live acceptance. Done on 2026-06-21.
6. Real Image Edit provider smoke. Done on 2026-06-21.
7. Real repair workflow with second Quality Verifier. Done on 2026-06-21.
8. One real Try-On generation smoke. Done on 2026-06-21.
9. Try-On service lifecycle with real Vertex generation and final quality verification. Done on 2026-06-21.
10. Deployed HTTP/worker Try-On route smoke with production runtime dependencies. Done on 2026-06-21.

## Stop Conditions

Stop live rollout if any of these happen:

- no-garment or multi-garment ambiguity passes as valid garment;
- material agent invents exact composition without trusted facts;
- instruction agent disables preservation constraints;
- quality verifier passes an obvious broken output;
- repair provider is called for face/body/pose failures;
- repaired result is exposed without second quality verification;
- credits are charged for pre-generation or system failures.

## Current Readiness Summary

The backend is locally protected against the main false-pass paths. Garment Identity, Material / Texture, Try-On Instruction, Quality Verifier, Repair Agent, Google GenAI image-edit smoke, real repair workflow with second Quality Verifier, one Vertex Virtual Try-On generation smoke, Try-On service lifecycle acceptance, and deployed HTTP/worker Try-On route smoke passed controlled VM validation. Broad production rollout is now blocked by deployment readiness work outside this Try-On backend gate: production backend/frontend deployment smoke, public URL checks, and frontend workflow integration verification.
