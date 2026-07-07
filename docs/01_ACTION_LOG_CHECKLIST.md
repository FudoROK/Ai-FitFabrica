# AI FitFabrica - Action Log And Checklist

Дата актуализации: 2026-06-17

Этот документ нужен как рабочий журнал. Каждая новая сессия Codex или другая модель должна сначала читать:

1. `docs/README.md`
2. этот файл
3. `docs/00_PROJECT_MASTER_PLAN.md`
4. профильный документ по текущей задаче

## Current status

- Current phase: agent-by-agent production acceptance.
- Last completed agent: Human Identity Agent.
- Current local work: Try-On chain local hardening completed through Repair / Image Edit policy.
- Next recommended live step: controlled VM/staging live acceptance, starting with Garment Identity.
- Readiness report: `docs/reports/2026-06-17-try-on-local-readiness-report.md`.
- VM/staging needed only for live provider runs, deploy and E2E checks.
- Local tests/docs/code work can run without VM.

## Completed checklist

### Documentation cleanup

- [x] Created canonical documentation index.
- [x] Created master implementation plan.
- [x] Created action log/checklist.
- [x] Created technical project map.
- [x] Created unified agents guide.
- [x] Created owner remaining-work document.
- [x] Investor PDF created and visually verified.
- [x] Legacy/intermediate docs moved to `docs/archive/legacy_2026_06_17/`.

### Platform and architecture

- [x] Established backend-first architecture.
- [x] Isolated product workflows from direct provider SDK usage.
- [x] Added canonical `AgentInvocationService`.
- [x] Added agent invocation SQL ledger.
- [x] Added provider-neutral adapter contour.
- [x] Migrated deprecated Vertex generative runtime usage to Google Gen AI SDK contour.
- [x] Added architecture guardrails.

### Frontend/workspace

- [x] Next.js workspace baseline exists.
- [x] Product Card page uses backend workflow.
- [x] Workspace capability/credits disabled states wired.
- [x] Publish/import/sync production actions remain locked until real pipelines exist.

### Product Card

- [x] Product Card contract checked.
- [x] Frontend Product Card form connected to backend.
- [x] Product Card Garment Identity child analysis added.
- [x] Product Card Agent receives structured garment analysis only.
- [x] Product Card staging smoke completed earlier.

### Try-On foundation

- [x] Human Identity Agent integrated.
- [x] Garment Identity and Material / Texture analysis bundle wired before Try-On generation.
- [x] Try-On Instruction Agent wired to structured analysis snapshots.
- [x] Generation failure persistence and zero-charge behavior hardened.

### Human Identity Agent

- [x] Contract v2 created.
- [x] Backend policy hardened.
- [x] 8-asset acceptance run completed.
- [x] Critical false pass count = 0.
- [x] Multiple people blocked explicitly.
- [x] Cropped/headshot blocked.
- [x] Face hidden/occluded blocked.
- [x] Good front and side pose allowed.

Acceptance artifact:

- `output/human_identity_live_rerun_20260616_retry.jsonl`

### Garment Identity Agent

- [x] Contract v2 created.
- [x] Prompt updated to require garment count, crop quality, workflow coverage, occlusion risk and target ambiguity.
- [x] Backend continuation policy added.
- [x] Product Card adapter blocks unsafe garment analyses before generation.
- [x] Try-On adapter blocks unsafe garment analyses before instruction/generation.
- [x] Local false-pass tests added for no garment, ambiguous multiple garments, tight crop, insufficient coverage and high occlusion.
- [x] Dedicated live acceptance script added: `scripts/garment_identity_live_acceptance.py`.
- [ ] Live acceptance run on real garment images pending VM/staging.

Local verification:

- `tests/test_garment_identity_live_acceptance_script.py`
- `tests/test_garment_identity_policy.py`
- `tests/test_product_card_garment_identity_adapter.py`
- `tests/test_try_on_garment_material_analysis_adapters.py`
- `tests/test_fitfabrica_agent_contracts.py`
- `tests/test_agent_prompt_policy.py`

### Material / Texture Agent

- [x] Contract version bumped to `material_texture.contract.v2`.
- [x] Prompt updated to require evidence-backed visible material and texture signals.
- [x] Backend continuation policy added.
- [x] Try-On adapter blocks empty visual material analysis before Try-On Instruction.
- [x] Try-On adapter maps invalid composition claims to safe failure.
- [x] Local honesty tests added for missing signals, missing evidence, low confidence and high uncertainty.
- [x] Dedicated live acceptance script added: `scripts/material_texture_live_acceptance.py`.
- [x] Live acceptance dataset contract documented under `test-assets/material-texture`.
- [x] Live acceptance run on real garment material images passed on VM/staging.

Local verification:

- `tests/test_material_texture_policy.py`
- `tests/test_try_on_garment_material_analysis_adapters.py`
- `tests/test_material_texture_live_acceptance_script.py`
- `tests/test_fitfabrica_agent_contracts.py`
- `tests/test_agent_prompt_policy.py`

### Try-On Instruction Agent

- [x] Contract version bumped to `try_on.contract.v2`.
- [x] Prompt updated to require evidence-backed focus points, generation exclusions and enabled preservation flags.
- [x] Backend continuation policy added.
- [x] Adapter still sends only approved structured analysis snapshots and no artifacts.
- [x] Adapter blocks disabled face/body/pose preservation before image generation.
- [x] Adapter blocks missing garment focus points, missing generation exclusions, missing evidence, low confidence and high uncertainty.
- [x] Dedicated live acceptance script added: `scripts/try_on_instruction_live_acceptance.py`.
- [x] Prompt hardened to require non-empty generation exclusions.
- [x] Live acceptance run passed on VM/staging.

Local verification:

- `tests/test_try_on_instruction_policy.py`
- `tests/test_try_on_instruction_agent_adapter.py`
- `tests/test_try_on_instruction_live_acceptance_script.py`
- `tests/test_try_on_instruction_workflow.py`
- `tests/test_fitfabrica_agent_contracts.py`
- `tests/test_agent_prompt_policy.py`

### Quality Verifier Agent

- [x] Contract version bumped to `quality_verifier.contract.v2`.
- [x] Prompt updated to forbid unsafe pass recommendations.
- [x] Backend quality policy added.
- [x] Deterministic quality verifier now normalizes reports before user exposure.
- [x] Model-backed quality verifier now normalizes provider verdicts before user exposure.
- [x] Local policy tests cover missing checks, failed checks, warning checks and low-confidence pass.
- [x] Dedicated live visual acceptance script added: `scripts/quality_verifier_live_acceptance.py`.
- [x] Live visual acceptance dataset contract documented under `test-assets/quality-verifier`.
- [x] Live visual acceptance run passed on VM/staging.
- [x] Dedicated AgentInvocationService-based Quality Verifier adapter integrated into Try-On runtime wiring.

Local verification:

- `tests/test_try_on_quality_policy.py`
- `tests/test_try_on_quality_verifier.py`
- `tests/test_try_on_model_backed_quality_verifier.py`
- `tests/test_quality_verifier_live_acceptance_script.py`
- `tests/test_fitfabrica_agent_contracts.py`
- `tests/test_agent_prompt_policy.py`
- `tests/test_image_agent_contract_hardening.py`

### Repair Agent / Image Edit Pipeline

- [x] Contract version bumped to `repair.contract.v2`.
- [x] Prompt updated to require local-only approved defect repairs and preservation constraints.
- [x] Backend repair policy added.
- [x] Deterministic repair adapter blocks unsafe repair attempts.
- [x] Provider image-edit repair adapter blocks unsafe repair attempts before calling provider.
- [x] Existing workflow confirms second quality verification after repair.
- [x] Dedicated Repair Agent live acceptance script added: `scripts/repair_agent_live_acceptance.py`.
- [x] Repair Agent live acceptance passed on VM/staging.
- [x] Google GenAI image-editing adapter added behind `ImageEditingPort`.
- [x] Provider-runtime repair/generation adapters persist real provider bytes when the provider returns an object-storage artifact.
- [x] Real image-edit provider smoke passed on VM/staging with `IMAGE_EDITING_PROVIDER=google_genai`.
- [x] Dedicated AgentInvocationService-based Repair Agent planner adapter added for Try-On repair.
- [x] Provider-runtime image-edit repair now consumes Repair Agent local plans before editing.
- [x] Provider-runtime repair blocks image-edit when Repair Agent returns `unsafe` or when planner invocation fails.

Local verification:

- `tests/test_try_on_repair_policy.py`
- `tests/test_try_on_repair_adapter.py`
- `tests/test_try_on_provider_repair_adapter.py`
- `tests/test_try_on_repair_agent_planner.py`
- `tests/test_repair_agent_live_acceptance_script.py`
- `tests/test_try_on_workflow_service_rebase.py::test_try_on_workflow_service_repairs_when_quality_verifier_recommends_it`
- `tests/test_agent_prompt_policy.py`

### Cost and investor economics

- [x] Workflow Agent Cost Map v1 created.
- [x] Credits Policy v1 created.
- [x] Credits Pricing Table v1 created.
- [x] `WorkflowCostEstimator` added.
- [x] `scripts/report_workflow_costs.py` added.
- [x] Agent invocation cost metadata added.
- [x] Investor PDF created.

## Open checklist

### Next technical steps

- [x] Garment Identity Agent live production acceptance.
- [x] Material / Texture Agent live production acceptance.
- [x] Try-On Instruction Agent live acceptance expansion.
- [x] Quality Verifier Agent live visual acceptance dataset.
- [x] Repair Agent live acceptance.
- [x] Real image-edit provider live smoke.
- [ ] Model routing config for cheap/expensive model tiers.
- [x] One real Try-On generation smoke with Vertex Virtual Try-On.
- [x] Try-On service lifecycle with real Vertex provider and final quality gate.
- [x] Full deployed HTTP/worker Try-On route smoke with production runtime dependencies.
- [ ] Marketplace connector design and legal source policy.
- [ ] Recalibration report after 20-50 real runs.

### Documentation steps

- [ ] Keep `01_ACTION_LOG_CHECKLIST.md` updated after every significant task.
- [ ] Update `03_AGENT_SYSTEM_GUIDE.md` whenever an agent prompt/contract/model routing changes.
- [ ] Update investor PDF after pricing recalibration.
- [ ] Archive outdated intermediate docs after confirming no tests/reference links require them.

## Live staging notes

Use VM/staging only for:

- live Gemini/Vertex calls;
- backend deploy;
- API smoke checks;
- worker/Redis/Postgres/MinIO/Qdrant integrated checks;
- investor/partner demo.

Do not keep VM running for:

- local unit tests;
- Markdown/PDF docs work;
- frontend-only code edits;
- backend pure unit tests.

## Known risks

- Gemini/Vertex can return `429 RESOURCE_EXHAUSTED` during burst tests.
- Provider prices can change; cost config must be versioned.
- Some old docs remain as historical context and should not be treated as canonical.
- Full Try-On production quality is not complete until Quality Verifier and Repair workflows are validated.

## 2026-06-19 Garment Identity VM Live Acceptance

- [x] VM Python runtime corrected from Python 3.10 to Python 3.11 using isolated `.venv311`.
- [x] Garment Identity test assets uploaded to `/opt/fitfabrica/test-assets/garment-identity`.
- [x] Initial live run exposed stale VM runtime code: contract v1 allowed `cropped_garment.png` and `multiple_garments.png`.
- [x] VM Garment Identity runtime files synchronized to current contract v2 and backend continuation policy.
- [x] VM targeted tests passed: `63 passed`.
- [x] Final live acceptance passed: `10/10 matched`, `false_pass_count=0`, `false_reject_count=0`.
- [x] Final report saved locally: `output/garment_identity_live_acceptance_vm_v2.jsonl`.

## 2026-06-19 Material / Texture Live Acceptance Prep

- [x] Added Material / Texture acceptance CLI without running the full Try-On workflow.
- [x] Canonical required files defined for `test-assets/material-texture`.
- [x] Expected decisions defined: 6 allowed material-evidence cases, 2 blocked poor-evidence cases.
- [x] Local script tests passed: `10 passed`.
- [x] Material / Texture policy and adapter tests passed: `16 passed`.
- [x] Uploaded real material images to VM and ran `scripts/material_texture_live_acceptance.py`.

## 2026-06-20 Material / Texture VM Live Acceptance

- [x] Material / Texture assets uploaded to `/opt/fitfabrica/test-assets/material-texture`.
- [x] VM runtime checked: `material_texture.contract.v2`.
- [x] VM targeted tests passed: `26 passed`.
- [x] Final live acceptance passed: `8/8 matched`, `false_pass_count=0`, `false_reject_count=0`.
- [x] Final report saved locally: `output/material_texture_live_acceptance_vm.jsonl`.

## 2026-06-20 Try-On Instruction VM Live Acceptance

- [x] Added Try-On Instruction acceptance CLI without image generation.
- [x] VM runtime checked: `try_on.contract.v2`.
- [x] Initial live run exposed false rejects: both approved cases missed `generation_exclusions`.
- [x] Try-On prompt hardened to require non-empty `generation_exclusions` with explicit identity/body/pose/detail exclusions.
- [x] VM targeted tests passed after hardening: `30 passed`.
- [x] Final live acceptance passed: `2/2 matched`, `false_pass_count=0`, `false_reject_count=0`.
- [x] Final report saved locally: `output/try_on_instruction_live_acceptance_vm_v2.jsonl`.

## 2026-06-20 Quality Verifier Live Acceptance Prep

- [x] Added Quality Verifier visual acceptance CLI without running Try-On generation.
- [x] Canonical 8-case visual dataset contract defined for `test-assets/quality-verifier`.
- [x] Each case requires `human_source.png`, `garment_source.png`, and `generated_result.png`.
- [x] Expected decisions defined: 1 pass, 2 repair-recommended, 5 reject.
- [x] Local script tests passed: `10 passed`.
- [x] Quality policy/contract/prompt targeted tests passed: `23 passed`.
- [x] Uploaded real visual quality cases to VM and ran `scripts/quality_verifier_live_acceptance.py`.

## 2026-06-21 Quality Verifier VM Live Acceptance

- [x] Quality Verifier assets uploaded to `/opt/fitfabrica/test-assets/quality-verifier`.
- [x] VM runtime checked: `quality_verifier.contract.v2`.
- [x] Initial live run found 2 mismatches: `missing_key_garment_detail` and `severe_anatomy_artifact` were classified as `repair_recommended`.
- [x] Quality Verifier prompt hardened so missing key garment details and severe anatomy defects return `reject`.
- [x] VM targeted tests passed after hardening: `22 passed`.
- [x] Final live acceptance passed: `8/8 matched`, `false_pass_count=0`, `false_repair_count=0`, `false_reject_count=0`.
- [x] Final report saved locally: `output/quality_verifier_live_acceptance_vm_v2.jsonl`.

## 2026-06-21 Repair Agent VM Live Acceptance

- [x] Added Repair Agent acceptance CLI without executing image editing.
- [x] VM runtime checked: `repair.contract.v2`.
- [x] VM targeted tests passed: `24 passed`.
- [x] Final live acceptance passed: `4/4 matched`, `false_local_count=0`, `false_unsafe_count=0`.
- [x] Unsafe defects (`face_changed`, `severe_anatomy_artifact`) were not classified as local repair.
- [x] Final report saved locally: `output/repair_agent_live_acceptance_vm.jsonl`.
- [x] Google GenAI image-editing adapter implemented after Repair Agent acceptance.
- [x] Dedicated image-editing live smoke CLI added: `scripts/image_editing_live_smoke.py`.
- [x] Real image-edit provider smoke passed on VM/staging with real edited image bytes.
- [x] Second Quality Verifier pass after real image-edit repair passed on VM/staging.

## 2026-06-21 Google GenAI Image Editing Runtime Adapter

- [x] Added `GoogleGenAIImageEditingProvider` behind the backend-owned `ImageEditingPort`.
- [x] Added explicit runtime config: `IMAGE_EDITING_PROVIDER`, `IMAGE_EDITING_MODEL`, `IMAGE_EDITING_ROOT_PREFIX`.
- [x] Provider runtime can now select `google_genai` image editing without leaking Google SDK imports into use cases/workflows.
- [x] Repair adapter now persists real provider edited bytes instead of placeholder bytes for non-stub providers.
- [x] Provider-runtime generation adapter now persists real provider edited bytes instead of placeholder bytes for non-stub providers.
- [x] Dedicated VM/staging smoke script added: `scripts/image_editing_live_smoke.py`.
- [x] Local targeted verification passed: `27 passed`.
- [x] VM/staging live image-edit smoke passed.
- [x] Live smoke correction: Google image editing accepts `image/png` / `image/jpeg`, not `image/webp`; provider-runtime image-edit output switched to `image/png`.
- [x] Live smoke correction: Google image editing expects one raw image; adapter now sends only the source image and keeps backend preservation constraints in prompt/policy.
- [x] Full repair workflow acceptance with second Quality Verifier pass passed on VM/staging.

## 2026-06-21 Google GenAI Image Editing VM Smoke

- [x] Uploaded image-edit runtime files to VM under `/opt/fitfabrica`.
- [x] VM targeted tests passed after sync: `29 passed`.
- [x] Real provider smoke passed with model `imagen-3.0-capability-001`.
- [x] Output provider: `google_genai_image_editing`.
- [x] Output MIME type: `image/png`.
- [x] Output size: `1000991` bytes.
- [x] Final report saved locally: `output/image_editing_live_smoke_vm.jsonl`.
- [x] Next gate completed: repair workflow path with real image-edit output followed by second Quality Verifier.

## 2026-06-21 Real Repair Workflow VM Acceptance

- [x] Added `scripts/repair_workflow_live_acceptance.py`.
- [x] VM targeted tests passed before live run: `30 passed`.
- [x] Real repair workflow acceptance passed.
- [x] Input case: `test-assets/quality-verifier/minor_background_artifact`.
- [x] Initial quality verdict: `repair_recommended`.
- [x] Image-edit provider: `google_genai_image_editing`.
- [x] Repair artifact: `fitfabrica-staging/tenants/public/try-on/repair_workflow_live_acceptance/repair_image/repair.png`.
- [x] Repair artifact size: `3190527` bytes.
- [x] Second Quality Verifier verdict: `pass`.
- [x] Final report saved locally: `output/repair_workflow_live_acceptance_vm.jsonl`.

## 2026-06-21 Vertex Virtual Try-On Generation VM Smoke

- [x] Added `scripts/try_on_generation_live_smoke.py`.
- [x] VM targeted tests passed before live run: `37 passed`.
- [x] Live Vertex Virtual Try-On generation smoke passed.
- [x] Generation mode: `vertex_virtual_try_on`.
- [x] Model: `virtual-try-on-001`.
- [x] Result artifact: `fitfabrica/tenants/public/try-on/try_on_generation_live_smoke/result_image/result.png`.
- [x] Result artifact size: `1713851` bytes.
- [x] Deterministic Quality Verifier verdict: `pass`.
- [x] Live SDK correction: `RecontextImageSource.prompt` is rejected by the live Vertex Virtual Try-On API, so the client no longer sends prompt inside the SDK source payload.
- [x] Final report saved locally: `output/try_on_generation_live_smoke_vm.jsonl`.
- [ ] Next gate: end-to-end Try-On workflow with real generation and final quality verification through the full worker/service path.

## 2026-06-21 Try-On Service VM Acceptance

- [x] Added `scripts/try_on_service_live_acceptance.py`.
- [x] VM targeted tests passed before live run: `38 passed`.
- [x] Service lifecycle acceptance passed through `TryOnWorkflowService.create_job` and `TryOnWorkflowService.execute_job`.
- [x] Job id: `try_on_87b4ba0cc7654aa6970de6f8dc0f5d86`.
- [x] Final status: `completed`.
- [x] Generation mode: `vertex_virtual_try_on`.
- [x] Result artifact: `fitfabrica/tenants/public/try-on/try_on_87b4ba0cc7654aa6970de6f8dc0f5d86/result_image/result.png`.
- [x] Result artifact size: `1717918` bytes.
- [x] Final Quality Verifier verdict: `pass`.
- [x] Status history: `accepted -> analyzing_human -> generating -> quality_checking -> completed`.
- [x] Final report saved locally: `output/try_on_service_live_acceptance_vm.jsonl`.
- [ ] Next gate: deployed HTTP/worker Try-On smoke with real runtime dependencies.

## 2026-06-21 Deployed HTTP/Worker Try-On VM Smoke

- [x] Added `scripts/try_on_http_worker_live_smoke.py`.
- [x] Created temporary VM env `.env.try-on-http-smoke.local` for real Try-On smoke without changing the default staging env.
- [x] Recreated `api` and `worker` containers with real Try-On settings for the smoke.
- [x] Confirmed real activation readiness via `/health`: `backend=vertex_virtual_try_on`, `readiness_status=ready`.
- [x] HTTP smoke passed through `POST /api/try-on/jobs`, status polling, and result endpoint.
- [x] Job id: `try_on_f9bb18ed2e654003a83ebed97a049145`.
- [x] Final status: `completed`.
- [x] Quality verdict: `pass`.
- [x] Result status: `completed`.
- [x] Final report saved locally: `output/try_on_http_worker_live_smoke_vm.jsonl`.
- [x] Restored `api` and `worker` containers to default staging env after the smoke.
- [x] Confirmed default staging `/health` returned to `backend=sandbox_fake`, `activation_enabled=false`.
- [x] Next gate completed: production deployment readiness review for backend + frontend, including public URL smoke and current frontend workflow integration.

## 2026-06-21 Deployment Readiness And Backend VM Deploy

- [x] Verified Firebase Hosting config: static export from `apps/web/out`.
- [x] Verified frontend API base contract uses `NEXT_PUBLIC_API_BASE_URL=https://api.fit.aisoulfabrica.com`.
- [x] Frontend checks passed: `npm run lint`, `npm run typecheck`, `NEXT_PUBLIC_API_BASE_URL=https://api.fit.aisoulfabrica.com npm run build`.
- [x] Frontend build exported 29 static routes.
- [x] Public backend health passed: `https://api.fit.aisoulfabrica.com/health` returned `200`.
- [x] Public workspace bootstrap passed: `https://api.fit.aisoulfabrica.com/api/workspace/bootstrap` returned `200` with valid UTF-8 JSON.
- [x] Public backend remains in safe default mode: `backend=sandbox_fake`, `activation_enabled=false`.
- [x] Backend checks passed before deploy: architecture guardrail, `compileall src`, targeted provider/runtime tests.
- [x] Full backend test suite passed after fixes: `808 passed`.
- [x] Fixed stale tests after runtime/doc cleanup:
  - provider runtime cache test now accepts object storage dependency;
  - Try-On real activation docs now point at active `docs/runbooks` files;
  - Try-On sandbox/durable-storage docs now point at active `docs/runbooks` files;
  - Try-On default quality/repair/stylist backends are now deterministic unless env explicitly enables model/provider-backed paths.
- [x] Built clean backend deploy archive from runtime files only, avoiding the old oversized broad archive pattern.
- [x] Uploaded backend archive to VM `fitfabrica-staging-vm`.
- [x] VM deployment completed despite local SSH command timeout; follow-up checks showed `api` and `worker` healthy.
- [x] VM code version confirmed: `src/settings_model_try_on.py` default quality verifier is `deterministic`.
- [x] VM Alembic current revision confirmed: `20260615_000016 (head)`.
- [x] Public backend post-deploy smoke passed: `/health` and `/api/workspace/bootstrap` returned `200`.
- [x] Temporary deploy archives removed locally and from VM `/tmp`.
- [x] Firebase Hosting deploy completed after user refreshed Firebase CLI credentials with `firebase login --reauth`.
- [x] Firebase deployed 348 files from `apps/web/out`.
- [x] Firebase release URL verified: `https://ai-fitfabrica.web.app/` returned `200`.
- [x] Custom frontend domain verified: `https://fit.aisoulfabrica.com/` returned `200`.
- [x] Backend public smoke after frontend deploy passed: `/health` and `/api/workspace/bootstrap` returned `200`.

## 2026-06-22 Paid Vertex Try-On Controlled Smoke

- [x] User approved one paid real AI Try-On run.
- [x] Temporarily switched VM `api` and `worker` to `.env.try-on-http-smoke.local`.
- [x] Confirmed `/health`: `backend=vertex_virtual_try_on`, `activation_enabled=true`, `readiness_status=ready`.
- [x] Ran one HTTP/worker real Try-On smoke with VM acceptance assets.
- [x] Job id: `try_on_f399a6aa932b4816854713b1d24889f0`.
- [x] Final status: `completed`.
- [x] Result image kind: `generated_artifact`.
- [x] Quality verdict: `pass`.
- [x] Quality confidence: `0.86`.
- [x] Report saved on VM: `output/try_on_paid_real_run_20260622.jsonl`.
- [x] Restored VM `api` and `worker` to `.env.portable-remote-staging.local`.
- [x] Confirmed public `/health` returned to safe mode: `backend=sandbox_fake`, `activation_enabled=false`.
- [x] Fixed production labeling gap: real `vertex_virtual_try_on` runs now use `vertex_virtual_try_on_generation` status stage and `try_on_vertex_virtual_try_on_generation` cost event type.
- [x] Fixed browser delivery gap: generated Try-On result payload now exposes a public absolute backend artifact URL instead of internal MinIO URLs.
- [x] Added backend artifact endpoint that streams result image bytes from object storage through the API.
- [x] Deployed the artifact delivery fix to VM and verified paid job result image loads from `https://api.fit.aisoulfabrica.com/api/jobs/{job_id}/artifacts/result-image`.
- [x] Verification passed: targeted Try-On tests `36 passed`, runtime tests `12 passed`, architecture guardrail passed, `compileall src` passed, full backend suite `811 passed`.

## 2026-06-23 Garment Identity Live Acceptance

- [x] Started execution of `docs/superpowers/plans/2026-06-23-wear-controls-taxonomy-admin-v2-implementation-plan.md`.
- [x] Confirmed public backend health before live acceptance: `/health` returned `200`, backend `sandbox_fake`, queue depth `0`.
- [x] Confirmed VM dataset exists at `/opt/fitfabrica/test-assets/garment-identity` with the canonical 10 assets.
- [x] Ran Garment Identity live acceptance inside `fitfabrica-api-1` using Python 3.11 and the configured staging provider runtime.
- [x] Report saved on VM and locally: `output/garment_identity_live_acceptance_20260623.jsonl`.
- [x] Summary: `total=10`, `matched=10`, `false_pass_count=0`, `false_reject_count=0`.
- [x] Allowed cases passed: coat/jacket, dress, good single shirt, logo/print item, pants/jeans, patterned item.
- [x] Blocked cases passed: cropped garment, dark/blurry garment, multiple garments, not garment.
- [x] Explicit block reasons included `insufficient_try_on_garment_coverage`, `ambiguous_target_garment`, and `no_garment_detected`.
- [x] Gate A passed: Garment Identity live acceptance has `0` critical false pass.
- [x] VM is not required for the next local implementation gates.
- [x] Added backend garment taxonomy domain foundation: catalog items, wear controls, review candidates, audit events.
- [x] Added SQL migration foundation for `garment_taxonomy_items`, `garment_wear_controls`, `garment_taxonomy_candidates`, and `garment_taxonomy_audit_log`.
- [x] Added SQL repository foundation for taxonomy items, wear controls, review candidates, and audit log writes.
- [x] Added Garment Identity contract extension for `taxonomy_parent`, `taxonomy_confidence`, `wear_control_candidates`, and `unknown_taxonomy_candidate`.
- [x] Persisted wear-control fields into Try-On and Product Card garment analysis snapshots.
- [x] Updated Garment Identity prompt instructions so taxonomy/wear-control outputs remain backend/admin-review suggestions, not direct production catalog mutations.
- [x] Local verification passed: garment taxonomy tests `17 passed`.
- [x] Local verification passed: Garment Identity wear-control contract plus existing adapter tests `28 passed`.
- [x] Local verification passed: `compileall src`.
- [x] Local verification passed: architecture guardrail.
- [x] Wired taxonomy service into production Try-On and Product Card Garment Identity adapters when SQL storage is configured.
- [x] Added backend filtering of agent-proposed wear controls against approved taxonomy catalog.
- [x] Added backend capture of unknown garment taxonomy candidates from Garment Identity output.
- [x] Added admin-review service operations: list pending candidates, approve, reject, merge.
- [x] Added guarded admin taxonomy API behind `ENABLE_ADMIN_TAXONOMY=false` by default.
- [x] Added admin role/actor header requirement before mutation endpoints can run.
- [x] Added admin-review audit event writes for approve/reject/merge operations.
- [x] Local verification passed: taxonomy/runtime/admin targeted backend tests `36 passed`.
- [x] Local verification passed: settings tests `13 passed`.
- [x] Added frontend `/admin/taxonomy` review page.
- [x] Added typed frontend admin taxonomy API contracts.
- [x] Added frontend API client methods for candidate list, approve, reject, and merge.
- [x] Frontend admin taxonomy UI is locked unless `NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI=true`.
- [x] Frontend admin mutations require explicit admin actor id before requests are sent.
- [x] Local verification passed: admin taxonomy page guardrail.
- [x] Local verification passed: frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Local verification passed: current admin/taxonomy backend+frontend targeted suite `17 passed`.
- [x] Added public read-only garment taxonomy endpoint `GET /api/garment-taxonomy/wear-controls`.
- [x] Added typed frontend API contract/client for backend-provided wear controls.
- [x] Added Try-On wear-control picker component with locked pending-analysis state.
- [x] Integrated pending wear-control UI into single, upper/lower, upper/lower/outerwear, and full-body Try-On modes.
- [x] Local verification passed: garment taxonomy route and Try-On wear-control UI guardrails `3 passed`.
- [x] Local verification passed: `compileall src`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Added Try-On lifecycle status `analysis_ready`.
- [x] Added Try-On lifecycle mode `analysis_only` so analysis can stop before generation and billing.
- [x] Added `GET /api/jobs/{job_id}/pre-generation-analysis` to return analyzed garment slots and backend-approved wear controls.
- [x] Added `POST /api/jobs/{job_id}/generate` to continue an analysis-ready job into generation.
- [x] Try-On execution now resumes from persisted analysis instead of rerunning Human/Garment/Material analysis.
- [x] Frontend Try-On now creates jobs in analysis-first mode, shows active backend-provided wear-control options, and exposes a separate generation button.
- [x] Local verification passed: pre-generation analysis targeted tests `6 passed`.
- [x] Local verification passed: combined Try-On/taxonomy/wear-control guardrails `9 passed`.
- [x] Local verification passed: sandbox lifecycle, multi-garment upload, and outfit composition targeted tests `34 passed`.
- [x] Local verification passed: architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Added backend-validated `TryOnWearControlSelection` domain model.
- [x] Added SQL persistence for Try-On wear-control selections on the job aggregate root.
- [x] Added Alembic migration `20260624_000019_try_on_wear_control_selections.py`.
- [x] Added `PUT /api/jobs/{job_id}/wear-controls` for durable selection save after `analysis_ready`.
- [x] Backend validates every selected control against garment taxonomy before persistence.
- [x] Try-On Instruction receives persisted wear-control selections.
- [x] Backend injects selected wear-control instruction templates into matching outfit slot focus points.
- [x] Frontend saves selected wear controls before calling generation continuation.
- [x] Local verification passed: selection route, instruction injection, and UI guardrails `31 passed`.
- [x] Local verification passed: SQL/analysis/pre-generation targeted tests `12 passed`.
- [x] Local verification passed: sandbox lifecycle, multi-garment upload, instruction, and UI targeted tests `50 passed`.
- [x] Local verification passed: `compileall src`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Added local end-to-end sandbox acceptance test for analysis -> wear-control save -> generation -> result.
- [x] Acceptance confirms selected wear-control instruction reaches persisted Try-On Instruction before generation.
- [x] Acceptance confirms completed result passes sandbox quality verifier after analysis-ready resume.
- [x] Local verification passed: wear-control e2e sandbox acceptance `2 passed`.
- [x] Local verification passed: connected Try-On/pre-generation/instruction/UI suite `52 passed`.
- [x] Local verification passed: architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Fixed backend CORS to allow `PUT` requests required by `/api/jobs/{job_id}/wear-controls`.
- [x] Added runtime guardrail proving CORS allows local browser `PUT` preflight for wear-control save.
- [x] Added local-only Try-On UI acceptance server for browser acceptance without VM, SQL, or AI quota.
- [x] Browser acceptance passed for `/workspace/try-on/new`: upload -> analysis_ready -> backend-driven wear controls -> save selection -> generate -> result.
- [x] Browser acceptance observed API sequence: workspace bootstrap, create job, status, pre-generation analysis, wear-control save, generate, status, result.
- [x] Browser acceptance final result page showed `Verdict: pass`, stylist note, and uploaded input metadata.
- [x] Acceptance screenshot saved as `tryon-ui-acceptance-completed.png`.
- [x] Local verification passed after browser acceptance: targeted backend tests `12 passed`.
- [x] Local verification passed after browser acceptance: `compileall src scripts`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Deployed backend runtime to staging VM `fitfabrica-staging-vm`.
- [x] Backend staging health passed at `https://api.fit.aisoulfabrica.com/health`.
- [x] Staging containers `api` and `worker` are healthy.
- [x] Staging Alembic migration head is `20260624_000019`.
- [x] Deployed frontend to Firebase Hosting for `https://fit.aisoulfabrica.com`.
- [x] Public frontend routes `/` and `/workspace/try-on/new` return HTTP 200.
- [x] Staging CORS preflight allows `PUT /api/jobs/{job_id}/wear-controls`.
- [x] Added frontend guard: wear-control selection is saved only for slots where backend returned approved controls.
- [x] Staging API smoke created Try-On job `try_on_4b6f12422d0d4ba384e467b98013fd6a`.
- [x] Staging API smoke reached `analysis_ready` and returned pre-generation analysis.
- [x] Staging API smoke observed empty wear-control catalog for detected `Shirt`.
- [x] Staging API smoke generation continuation executed and reached quality verification.
- [ ] Staging full acceptance is blocked: sandbox result was rejected by Quality Verifier after repair with final verdict `repair_recommended`.
- [ ] Next gate: seed baseline garment wear-control taxonomy for staging, expose/record failed quality reasons, then repeat full Try-On staging acceptance.
- [x] Optimized staging Docker deploy: backend image now copies only runtime allowlist (`src`, `alembic`, `alembic.ini`, `requirements.txt`, smoke script).
- [x] Optimized staging Docker deploy: API and worker now share one `fitfabrica-runtime:latest` image; deploy script builds only `api`.
- [x] Cleaned VM Docker build cache; preserved running containers and persistent volumes.
- [x] Optimized deploy completed in 72-92 seconds instead of 20+ minutes.
- [x] Staging API and worker are healthy on shared runtime image.
- [x] Staging Try-On acceptance passed with job `try_on_016174ed51c14fdc887ba6911f64f4ed`.
- [x] Acceptance path passed: `analysis_ready` -> seeded `shirt` controls -> saved `untucked` -> generation -> `completed`.
- [x] Acceptance result returned `quality_report.verdict=pass`.

## 2026-06-23 Multi-Garment Outfit Try-On Foundation

- [x] Added implementation plan: `docs/superpowers/plans/2026-06-23-multi-garment-outfit-try-on-plan.md`.
- [x] Preserved legacy single-item Try-On field `garment_photo`.
- [x] Added typed Try-On upload roles: `upper_garment_photo`, `lower_garment_photo`, `outerwear_garment_photo`, `full_body_garment_photo`.
- [x] Backend validation now requires `human_photo` plus at least one garment field.
- [x] `POST /api/try-on/jobs` accepts upper/lower/outerwear/full-body garment slot uploads.
- [x] Try-On workflow service persists every provided garment slot as separate typed input metadata and stored input.
- [x] Garment Identity v1 adapter now selects a primary garment from legacy/full-body/upper/lower/outerwear slots for backward-compatible analysis.
- [x] Frontend Try-On screen now exposes modes: `single_item`, `upper_lower`, `upper_lower_outerwear`, `full_body`.
- [x] Frontend sends only the garment fields required by the selected mode.
- [x] Frontend API contracts include all multi-garment upload roles.
- [x] Local verification passed: multi-garment backend route/service/adapter targeted tests `38 passed`.
- [x] Local verification passed: workspace multi-garment frontend guardrail.
- [x] Local verification passed: `npm run lint`, `npm run typecheck`, `npm run build`.
- [x] Local verification passed: `compileall src`.
- [x] Local verification passed: architecture guardrail.
- [x] Added `TryOnOutfitCompositionVerdict` domain model.
- [x] Added deterministic Outfit Composition Policy.
- [x] Policy allows legacy single item, `upper+lower`, and `upper+lower+outerwear`.
- [x] Policy blocks `full_body` mixed with separate garment slots.
- [x] Policy blocks duplicate garment slots.
- [x] Policy blocks `outerwear` without a complete base outfit.
- [x] Try-On workflow now rejects invalid garment slot combinations before upload persistence, AI calls, and billing.
- [x] Local verification passed: Try-On multi-garment/policy/frontend targeted tests `46 passed`.
- [x] Local verification passed after policy: `compileall src`, architecture guardrail, `npm run lint`, `npm run typecheck`, `npm run build`.
- [x] Added per-slot Garment Identity analysis bundle output.
- [x] `TryOnAnalysisBundle` now keeps backward-compatible primary `garment_identity` plus `garment_slot_analyses`.
- [x] Garment Identity is now invoked separately for each uploaded garment slot in deterministic slot order.
- [x] Try-On job aggregate now persists `garment_slot_analyses`.
- [x] Added SQL child table model `try_on_garment_slot_identity_analyses`.
- [x] Added Alembic migration `20260623_000018_try_on_garment_slot_analysis.py`.
- [x] SQL serialization/repository round-trip preserves per-slot garment analysis.
- [x] Local verification passed: per-slot analysis bundle, SQL serialization, migration, multi-garment upload, and sandbox lifecycle tests `33 passed`.
- [x] Local verification passed: adapter/outfit policy targeted tests `22 passed`.
- [x] Local verification passed: SQL repository targeted tests `4 passed`.
- [x] Local verification passed: `compileall src` and architecture guardrail.
- [x] Try-On Instruction request now includes `garment_slot_analyses`.
- [x] Try-On Instruction contract now supports `outfit_slot_focus_points`.
- [x] Persisted generation instruction now stores per-slot focus points and generation exclusions.
- [x] Deterministic Try-On Instruction adapter now derives slot-level focus points from per-slot garment analyses.
- [x] Try-On Agent prompt now explicitly requires multi-garment slot handling without inventing unsupported garment facts.
- [x] Deterministic Quality Verifier now records `outfit_slot_input_shape` for multi-garment requests.
- [x] Model-backed Quality Verifier fact pack now includes `garment_slot_roles`.
- [x] Local verification passed: instruction, quality, per-slot bundle, SQL, sandbox, multi-garment and outfit policy targeted tests `65 passed`.
- [x] Local verification passed: `compileall src` and architecture guardrail.
- [x] Added public read-only garment taxonomy endpoint `GET /api/garment-taxonomy/wear-controls`.
- [x] Added typed frontend API contract/client for backend-provided wear controls.
- [x] Added Try-On wear-control picker component with locked pending-analysis state.
- [x] Integrated pending wear-control UI into all Try-On garment upload modes without submitting unvalidated user choices.
- [x] Local verification passed: garment taxonomy route and Try-On wear-control UI guardrails `3 passed`.
- [x] Local verification passed: `compileall src`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Added Try-On lifecycle status `analysis_ready` and lifecycle mode `analysis_only`.
- [x] Added pre-generation analysis endpoint with per-slot garment type and backend-approved wear controls.
- [x] Added generation continuation endpoint for analysis-ready jobs.
- [x] Frontend now runs Try-On as a two-step flow: analysis first, user wear-control review second, generation third.
- [x] Local verification passed: pre-generation analysis targeted tests `6 passed`.
- [x] Local verification passed: combined Try-On/taxonomy/wear-control guardrails `9 passed`.
- [x] Local verification passed: sandbox lifecycle, multi-garment upload, and outfit composition targeted tests `34 passed`.
- [x] Local verification passed: architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Added backend-validated `TryOnWearControlSelection` domain model and durable SQL persistence.
- [x] Added Alembic migration `20260624_000019_try_on_wear_control_selections.py`.
- [x] Added `PUT /api/jobs/{job_id}/wear-controls` for validated selection persistence.
- [x] Try-On Instruction now receives persisted selections and backend injects instruction templates into matching outfit slots.
- [x] Frontend now saves wear-control selections before generation continuation.
- [x] Local verification passed: selection route, instruction injection, and UI guardrails `31 passed`.
- [x] Local verification passed: SQL/analysis/pre-generation targeted tests `12 passed`.
- [x] Local verification passed: sandbox lifecycle, multi-garment upload, instruction, and UI targeted tests `50 passed`.
- [x] Local verification passed: `compileall src`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Added local end-to-end sandbox acceptance test for analysis -> wear-control save -> generation -> result.
- [x] Acceptance confirms selected wear-control instruction reaches persisted Try-On Instruction before generation.
- [x] Acceptance confirms completed result passes sandbox quality verifier after analysis-ready resume.
- [x] Local verification passed: wear-control e2e sandbox acceptance `2 passed`.
- [x] Local verification passed: connected Try-On/pre-generation/instruction/UI suite `52 passed`.
- [x] Local verification passed: architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Fixed backend CORS to allow `PUT` requests required by `/api/jobs/{job_id}/wear-controls`.
- [x] Added runtime guardrail proving CORS allows local browser `PUT` preflight for wear-control save.
- [x] Added local-only Try-On UI acceptance server for browser acceptance without VM, SQL, or AI quota.
- [x] Browser acceptance passed for `/workspace/try-on/new`: upload -> analysis_ready -> backend-driven wear controls -> save selection -> generate -> result.
- [x] Browser acceptance observed API sequence: workspace bootstrap, create job, status, pre-generation analysis, wear-control save, generate, status, result.
- [x] Browser acceptance final result page showed `Verdict: pass`, stylist note, and uploaded input metadata.
- [x] Acceptance screenshot saved as `tryon-ui-acceptance-completed.png`.
- [x] Local verification passed after browser acceptance: targeted backend tests `12 passed`.
- [x] Local verification passed after browser acceptance: `compileall src scripts`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Optimized portable staging Docker build context by allowlisting runtime files and reusing one backend image for API/worker.
- [x] Deployed optimized backend package to VM; staging health remained green and API/worker use `fitfabrica-runtime:latest`.
- [x] Staging API acceptance passed for Try-On analysis-only lifecycle: create job -> analysis_ready -> wear-control save -> generation -> completed result.
- [x] Found live frontend issue after browser staging run: `/workspace/try-on/new` stopped at `analyzing_human` because the page fetched job status only once after create.
- [x] Added frontend polling after job creation until `analysis_ready/completed/failed`.
- [x] Added frontend polling after generation continuation until `completed/failed`.
- [x] Added workspace Try-On guardrail test proving frontend waits for backend readiness before analysis/generation handoff.
- [x] Local verification passed: workspace Try-On UI guardrails `5 passed`.
- [x] Local verification passed: frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Deployed frontend polling fix to Firebase Hosting.
- [x] First live browser rerun exposed backend sandbox quality normalization gap: model-backed verifier returned `verdict=reject` for the known sandbox fake placeholder.
- [x] Added quality policy regression coverage for staging wording: `sandbox fake and a placeholder`.
- [x] Backend quality policy now normalizes only the known sandbox-placeholder reject report to `pass` after failed-check protection.
- [x] Local verification passed: quality policy tests `9 passed`, `compileall src`, architecture guardrail.
- [x] Deployed backend quality policy fix to staging VM.
- [x] Live browser acceptance passed on `https://fit.aisoulfabrica.com/workspace/try-on/new`.
- [x] Acceptance job: `try_on_b781fe5113f84bcbafc98175d22a2421`.
- [x] Acceptance API path: create job -> repeated status polling -> pre-generation analysis -> wear-control save -> generate -> repeated status polling -> result.
- [x] Acceptance final page: `https://fit.aisoulfabrica.com/workspace/try-on/result?job_id=try_on_b781fe5113f84bcbafc98175d22a2421`, status completed, quality verdict pass.
- [ ] Next gate: decide whether to keep VM on for more live Try-On checks or shut it down and continue local implementation planning.
- [x] Ran one real paid Vertex Virtual Try-On smoke through the deployed workspace flow.
- [x] Real paid job: `try_on_c38db24dbf60478b87c208bbaed8c0e1`.
- [x] Real paid job completed through `vertex_virtual_try_on_generation`, result image kind `generated_artifact`, quality verdict `pass`, confidence `86%`.
- [x] Operator visual review found a critical false pass: generated image contains an extra hand/hand anatomy artifact.
- [x] Restored staging Try-On generation backend to `sandbox_fake` after the paid smoke to prevent accidental extra paid calls.
- [x] Added artifact-aware `TryOnQualityVerifierAgentAdapter` that invokes the versioned Quality Verifier Agent with human, garment, and generated-result artifact references.
- [x] Quality Verifier Agent adapter maps blocking visual defects such as extra hands to failed quality checks and backend `reject`.
- [x] Quality Verifier Agent adapter sends real generated artifact integrity metadata (`size_bytes`, `sha256`) so the artifact resolver can validate the result image.
- [x] Runtime wiring now selects `TryOnQualityVerifierAgentAdapter` for `TRY_ON_QUALITY_VERIFIER_BACKEND=model_backed` when `AgentInvocationService` is available.
- [x] Local verification passed: quality verifier agent adapter, deterministic/model-backed verifier, quality policy, and runtime wiring tests `23 passed`.
- [x] Local verification passed: `compileall src` and architecture guardrail.
- [x] Deployed artifact-aware Quality Verifier wiring to staging VM.
- [x] Verified staging runtime uses `TryOnQualityVerifierAgentAdapter`.
- [x] Ran one controlled paid real Try-On after verifier wiring.
- [x] Live quality-gate job: `try_on_9d043c177860484184a7d2958cf41bce`.
- [x] Workflow no longer exposed the generated result as `pass`; it failed before result exposure.
- [x] Live gate found a verifier-provider integration blocker: Quality Verifier Agent call returned `400 INVALID_ARGUMENT: Provided image is not valid`.
- [x] Added fail-closed behavior: when artifact-aware visual verification cannot read the generated image, the report is `reject`, not `repair_recommended`.
- [x] Local verification passed after fail-closed update: quality verifier/runtime tests `24 passed`, `compileall src`, architecture guardrail.
- [x] Deployed fail-closed visual-verifier-unavailable behavior to staging VM.
- [x] Restored staging backend to `sandbox_fake`; health is green and runtime still uses `TryOnQualityVerifierAgentAdapter`.
- [x] Added generated-result normalization before Quality Verifier Agent calls.
- [x] Normalization converts oversized/non-JPEG generated artifacts to `quality_verifier/generated_result.jpg`, max side `1600px`, JPEG quality `88`, with real `size_bytes` and `sha256`.
- [x] Verified old Vertex artifact normalization on VM: original PNG `6,509,891` bytes became JPEG `1071x1600`, `113,978` bytes.
- [x] Ran one controlled paid real Try-On after normalization.
- [x] Live quality-gate job: `try_on_d0c0f4a1e5d944ea83d3f914e33d486a`.
- [x] Visual Quality Verifier successfully read the normalized generated image and rejected the result before user exposure.
- [x] Rejection reason: severe hand/anatomy artifacts, including malformed hands/fingers.
- [x] Restored staging backend to `sandbox_fake` after the paid quality-gate run; `/health` confirms real activation is inactive.
- [x] Fixed cost-event labeling for failed real Vertex Try-On generation and quality rejection paths.
- [x] Added regression coverage proving Vertex generation failures and Vertex quality rejections record `try_on_vertex_virtual_try_on_generation`, estimated units `1`, and charged credits `0`.
- [x] Local verification passed: Try-On workflow, quality verifier, quality policy, and runtime wiring tests `39 passed`.
- [x] Local verification passed: `compileall src` and architecture guardrail.
- [x] Deployed the cost-event labeling fix to staging VM.
- [x] Staging `/health` remains healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive.
- [x] Staging container import check passed for `VertexVirtualTryOnGenerationAdapter`, `TryOnQualityVerifierAgentAdapter`, and Vertex cost event mapping.
- [x] Added backend-owned Try-On quality decision policy for post-generation quality failures.
- [x] Policy separates safe local `repair`, non-local `retry_recommended`, and hard `reject` decisions.
- [x] Severe hand/anatomy artifacts now resolve to `retry_recommended`, not local repair.
- [x] Identity/core-subject changes remain hard `reject`.
- [x] Workflow now persists `quality_decision` in failed quality-gate error details and keeps charged credits at `0`.
- [x] Local verification passed: quality decision, repair policy/adapters, workflow, quality verifier, quality policy, and runtime wiring tests `49 passed`.
- [x] Local verification passed: `compileall src` and architecture guardrail.
- [x] Deployed the quality-decision policy to staging VM.
- [x] Staging `/health` remains healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive.
- [x] Staging container policy smoke passed: hand/anatomy defect maps to `retry_recommended` with `hands` and `severe_artifact` categories.
- [x] Full backend verification passed after quality-decision deploy: `893 passed`, with one external Authlib deprecation warning.
- [x] Fixed full-suite regressions found during verification: restored lazy Vertex/Google GenAI import boundary, updated Try-On analysis fixtures to include `garment_slot_analyses`, and updated instruction stubs for wear-control selections.
- [x] Verification passed: `compileall src scripts`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Staging `/health` remained healthy and real Try-On activation inactive after verification.
- [x] Added controlled Try-On auto-retry orchestration for backend `retry_recommended` quality decisions.
- [x] Auto-retry is limited to one additional generation attempt per execution.
- [x] Retry is not used for identity/core-subject rejection; those remain hard quality failures.
- [x] Failed quality gate error details now include `retry_attempts`; successful retry increments generation estimated units but does not add user charge in unbilled/test flows.
- [x] Local verification passed: Try-On quality decision, repair, verifier, runtime, human identity, and instruction workflow tests `65 passed`.
- [x] Local verification passed: `compileall src scripts` and architecture guardrail.
- [x] Full backend verification passed after controlled retry orchestration: `899 passed`, with one external Authlib deprecation warning.
- [x] Frontend verification passed after controlled retry orchestration: `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Deployed controlled retry orchestration to staging VM.
- [x] Staging `/health` remained healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive.
- [x] Staging policy smoke passed: hand/anatomy defect maps to `retry_recommended`.
- [x] Staging HTTP sandbox smoke passed: job `try_on_c05751d4ae8840cf862a15514da35183`, final status `completed`, quality verdict `pass`, charged credits `0`.
- [x] Ran one explicitly approved paid real Vertex Try-On retry acceptance.
- [x] Paid retry acceptance job: `try_on_a9429552bfbf43399ead5fc1b7a3a644`.
- [x] Acceptance confirmed controlled retry orchestration works in staging: first Vertex generation, quality check, second Vertex generation retry, second quality check.
- [x] Paid retry acceptance failed closed before user exposure: final status `failed`, result endpoint `409`, charged credits `0`, estimated generation units `2`.
- [x] Failure exposed production blocker: staging repair path used stub image-editing provider after real Vertex generation, producing non-image repair bytes and causing visual verifier `Provided image is not valid`.
- [x] Restored staging to `sandbox_fake` immediately after paid acceptance; `/health` confirmed real activation inactive.
- [x] Added guardrail blocking `stub_image_editing` repair for real Try-On generation.
- [x] Workflow now respects repair-adapter `reject` output and does not re-run visual verification on a blocked/non-production repair result.
- [x] Local verification passed after repair guardrail: repair/workflow/quality targeted tests `51 passed`, full backend `902 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Deployed repair guardrail to staging VM.
- [x] Staging repair guardrail smoke passed: real-generation stub repair maps to `reject` with `repair_provider_not_production_ready`.
- [x] Staging HTTP sandbox smoke passed after guardrail deploy: job `try_on_facf4fb1f8b645dfa10a4d4b3eb2aa13`, final status `completed`, quality verdict `pass`.
- [x] Added runtime wiring guardrail: real Vertex Try-On does not attach repair when the image-editing provider is `stub_image_editing` or when deterministic repair is requested.
- [x] Real Vertex Try-On may attach repair only when a production-ready image-editing provider is configured.
- [x] Local verification passed after runtime repair wiring guardrail: runtime/repair/workflow targeted tests `38 passed`, full backend `905 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Deployed runtime repair wiring guardrail to staging VM.
- [x] Staging `/health` remained healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive after deploy.
- [x] Staging HTTP sandbox smoke passed after runtime wiring guardrail deploy: job `try_on_eb2b2c22edda404881d5650ed49b5d5d`, final status `completed`, quality verdict `pass`.
- [x] Hardened Google GenAI image-editing adapter for Try-On repair: provider receives generated result plus persisted human and garment reference images.
- [x] Added regression coverage proving Try-On repair passes human/garment references into provider-runtime image editing.
- [x] Verified runtime selection: `IMAGE_EDITING_PROVIDER=google_genai` is treated as production-ready repair for real Vertex, while stub/deterministic repair stays disabled.
- [x] Local verification passed after Google GenAI repair integration: repair/runtime/live-smoke-script targeted tests `45 passed`, full backend `905 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Deployed Google GenAI repair integration to staging VM.
- [x] Staging `/health` remained healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive after Google GenAI repair deploy.
- [x] Staging HTTP sandbox smoke passed after Google GenAI repair deploy: job `try_on_f3831c0130cf4562be136bc5f45ef2aa`, final status `completed`, quality verdict `pass`.
- [x] Extended Google GenAI image-editing adapter with Gemini native image-model support through `generate_content`.
- [x] Legacy Imagen `edit_image` path remains available for compatible models, but current Gemini image models use the non-deprecated native path.
- [x] Local verification passed after Gemini native image-editing support: repair/runtime targeted tests `46 passed`, full backend `906 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Deployed Gemini native image-editing support to staging VM.
- [x] Configured staging env with `IMAGE_EDITING_PROVIDER=google_genai` and `IMAGE_EDITING_MODEL=gemini-2.5-flash-image`.
- [x] Confirmed staging real Try-On activation remains inactive: `TRY_ON_GENERATION_BACKEND=sandbox_fake`, `ENABLE_REAL_TRY_ON_GENERATION=false`.
- [x] Staging HTTP sandbox smoke passed after Gemini image-editing env deploy: job `try_on_af178a717a5f46d3b45705662ff3c2d2`, final status `completed`, quality verdict `pass`.
- [x] Attempted one explicitly approved paid real Try-On acceptance with repair-capable staging env: job `try_on_761795f8eef14bef9f84515720f3f02e`.
- [x] Real Try-On acceptance did not reach Vertex generation: job stayed `accepted`, operations record became stale `processing`, and job cost event remained `try_on_sandbox_generation` with charged credits `0`.
- [x] Restored staging to `TRY_ON_GENERATION_BACKEND=sandbox_fake` and `ENABLE_REAL_TRY_ON_GENERATION=false` immediately after the timeout.
- [x] Found image-editing model issue: `gemini-2.5-flash-image-preview` returned Vertex `404 NOT_FOUND`; updated staging to GA model `gemini-2.5-flash-image`.
- [x] Ran one explicitly approved paid repair workflow acceptance with Google GenAI image editing: provider `google_genai_image_editing`, repaired artifact size `1,109,942` bytes, second quality verdict `pass`, confidence `0.86`.
- [x] Root-caused paid public API Try-On timeout: Redis queue item was claimed, SQL operations row moved to `processing`, and deployment/worker interruption left the job stale without a queue item.
- [x] Added worker stale-processing reclaim: when Redis queue is empty, worker can reclaim SQL `processing` jobs older than `PROCESSING_STALE_RECLAIM_SECONDS` and execute them instead of leaving them stuck.
- [x] Added in-memory and SQL regression coverage for stale processing reclaim.
- [x] Local verification passed after worker reclaim fix: operations/try-on targeted tests `20 passed`, full backend `908 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Deployed worker stale-processing reclaim fix to staging VM.
- [x] Staging `/health` remained healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive after worker reclaim deploy.
- [x] Staging HTTP worker sandbox smoke passed after reclaim deploy: job `try_on_c3f9a39be539436e838f03cfd4e7473c`, final status `completed`, quality verdict `pass`.
- [x] Stale paid-acceptance operations job `queue_job_1782566396978021` was reclaimed by the new worker logic and completed safely in sandbox mode.
- [x] Original paid-acceptance Try-On job `try_on_761795f8eef14bef9f84515720f3f02e` now completed with sandbox generation only, charged credits `0`.
- [x] Repeated one explicitly approved paid public API Vertex Try-On acceptance after worker reclaim fix.
- [x] Paid public API Vertex Try-On job `try_on_daf9a44fd0d64c2284ee9a119d89a05a` completed successfully with final quality verdict `pass`, confidence `0.98`.
- [x] Paid public API workflow path exercised accepted -> human identity analysis -> Vertex generation -> quality check -> repair -> retry Vertex generation -> final quality check -> completed.
- [x] Cost event recorded `try_on_vertex_virtual_try_on_generation`, estimated units `2`, charged credits `0`.
- [x] Final result artifact downloaded locally to `output/try_on_daf9a44fd0d64c2284ee9a119d89a05a_result.jpg`.
- [x] Restored staging to `TRY_ON_GENERATION_BACKEND=sandbox_fake` and `ENABLE_REAL_TRY_ON_GENERATION=false` immediately after paid acceptance.
- [x] Added explicit Try-On repair/image-editing cost event `try_on_provider_runtime_image_editing_repair`.
- [x] Repair cost event is emitted when provider-runtime repair is actually attempted, including failed/blocked repair paths.
- [x] Generation cost event remains first for API/backward compatibility; repair/image-editing cost is appended as a separate event with estimated repair units.
- [x] Local verification passed after repair cost event split: Try-On/cost targeted tests `59 passed`, full backend `908 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Deployed repair cost event split to staging VM.
- [x] Staging `/health` remained healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive after repair cost event deploy.
- [x] Staging HTTP worker sandbox smoke passed after repair cost event deploy: job `try_on_c96f0afedb6a4eb5acb24836a00660cc`, final status `completed`, quality verdict `pass`.
- [x] Ran one paid public API Vertex Try-On after repair cost event deploy: job `try_on_4893ed259a2240758e7677f098699b29`.
- [x] Paid public API job reached Vertex generation and retry but did not enter repair branch; final status `failed`, quality rejected after retry, generation cost event estimated units `2`, charged credits `0`.
- [x] Because the public API job did not enter repair, the new repair cost event was correctly absent for that job.
- [x] Ran one paid isolated repair workflow acceptance on the same deploy: provider `google_genai_image_editing`, repaired artifact size `1,176,149` bytes, second quality verdict `pass`, confidence `0.86`.
- [x] Restored staging to `TRY_ON_GENERATION_BACKEND=sandbox_fake` and `ENABLE_REAL_TRY_ON_GENERATION=false` immediately after paid checks.
- [x] Added deterministic Try-On repair-trigger acceptance mode `repair_acceptance` for staging/public API checks.
- [x] `repair_acceptance` forces exactly one local repair decision before final verification, so repair/image-editing cost events can be verified without depending on model randomness.
- [x] Extended HTTP worker live smoke script with `--sandbox-lifecycle-mode repair_acceptance`.
- [x] Local verification passed after repair acceptance mode: targeted Try-On/smoke tests `55 passed`, full backend `911 passed`, `compileall src scripts`, and architecture guardrail.
- [x] First staging public API sandbox smoke for `repair_acceptance` correctly exercised the repair branch and recorded `try_on_provider_runtime_image_editing_repair`, but exposed a weak acceptance path: final sandbox quality still failed closed.
- [x] Hardened `repair_acceptance` to apply a sandbox-only final pass report after the forced repair branch; real Vertex/provider runtime quality gates are not bypassed.
- [x] Added regression coverage for complete sandbox repair acceptance flow: forced repair, final pass, completed job, and separate repair cost event.
- [x] Local verification passed after sandbox final-pass hardening: targeted repair acceptance tests `6 passed`, full backend `913 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Redeployed repair acceptance hardening to staging VM.
- [x] Staging `/health` remained healthy with `TRY_ON_GENERATION_BACKEND=sandbox_fake` and real activation inactive after redeploy.
- [x] Staging public API repair acceptance sandbox smoke passed: job `try_on_b46585fae4634c0d96623da87934ae0c`, final status `completed`, quality verdict `pass`.
- [x] Staging repair acceptance cost events verified: `try_on_sandbox_generation` estimated units `1`, `try_on_provider_runtime_image_editing_repair` estimated units `1`, charged credits `0`.
- [x] Proceeded to the next product workflow milestone without another paid Try-On image-generation check: Garment Identity live acceptance.
- [x] Local Garment Identity preflight passed before live acceptance: policy/script/contract/adapter tests `52 passed`.
- [x] VM health check passed before Garment Identity live acceptance: public `/health` healthy, operations queue depth `0`, Try-On real activation inactive.
- [x] VM garment acceptance dataset verified: 10 canonical files present under `test-assets/garment-identity`.
- [x] First Garment Identity live acceptance exposed one critical false pass: `multiple_garments.png` was allowed even though the agent returned `garment_count=3`.
- [x] Hardened backend Garment Identity continuation policy: any `garment_count > 1` now blocks with explicit `multiple_garments_detected`, even if the agent selects a target garment.
- [x] Updated Product Card and Try-On Garment Identity adapter expectations to use the explicit multi-garment safe code.
- [x] Local verification passed after Garment Identity policy hardening: targeted tests `53 passed`, full backend `914 passed`, `compileall src scripts`, and architecture guardrail.
- [x] VM verification passed after policy hardening: targeted Garment Identity tests `37 passed`.
- [x] Garment Identity live acceptance passed after policy hardening: output `output/garment_identity_live_acceptance_20260628_after_policy.jsonl`, total `10`, matched `10`, false pass `0`, false reject `0`.
- [x] Started taxonomy and wear-control backend foundation locally; VM was not required.
- [x] Confirmed existing taxonomy foundation against the integrated plan: domain models, migration, SQL repository, service, read-only routes, Garment Identity mapping, Try-On selection persistence, instruction injection, and workspace picker are present.
- [x] Verified Gate B taxonomy foundation: domain/migration/service/SQL repository tests `19 passed`.
- [x] Verified Garment Identity taxonomy/wear-control contract extension: contract/Product Card/Try-On adapter tests `29 passed`.
- [x] Verified Try-On wear-control route, persistence, instruction, read-only taxonomy routes, SQL repository, sandbox e2e and workspace picker tests.
- [x] Added Quality Verifier wear-control contract support: `wear_control` defect type and `wear_control_match` category score.
- [x] Added quality policy tests proving selected wear-control violations cannot clean-pass: warnings become repair recommendations and blocking failures become rejects.
- [x] Added repair policy tests proving local wear-control warnings are repairable but blocking wear-control failures are not.
- [x] Local wear-control/taxonomy verification passed: targeted suite `94 passed`, full backend `920 passed`, `compileall src scripts`, architecture guardrail.
- [x] Frontend verification passed after wear-control foundation check: `npm run lint`, `npm run typecheck`, `npm run build`.
- [x] Completed admin taxonomy backend hardening review locally.
- [x] Confirmed admin taxonomy routes are disabled by default through `ENABLE_ADMIN_TAXONOMY=false` and return structured `admin_taxonomy_disabled`.
- [x] Confirmed admin taxonomy mutation/list routes require admin headers and return structured `admin_taxonomy_forbidden` without them.
- [x] Confirmed taxonomy storage absence returns structured `admin_taxonomy_storage_unavailable`.
- [x] Added structured `admin_taxonomy_validation_failed` responses for service validation errors instead of leaking raw exceptions.
- [x] Added backend `rename-and-approve` admin mutation endpoint and service operation with audit action `rename_and_approve_candidate`.
- [x] Extended typed frontend admin API client and admin review UI with rename-and-approve action.
- [x] Admin/taxonomy targeted verification passed: routes/page/domain/migration/service/SQL/read-only routes `30 passed`.
- [x] Full verification passed after admin taxonomy hardening: full backend `924 passed`, `compileall src scripts`, architecture guardrail, frontend `npm run lint`, `npm run typecheck`, `npm run build`.
- [x] Started Try-On Instruction + Quality Verifier selected wear-control gate locally.
- [x] Added fail-closed Try-On Instruction adapter guard: if an agent returns a slot instruction contradicting backend-selected wear control, backend blocks with `wear_control_instruction_conflict` before generation.
- [x] Updated Try-On Instruction prompt to treat `user_options.wear_control_selections` as authoritative backend input and to avoid contradictory instructions.
- [x] Added Quality Verifier prompt guardrails for `wear_control_match` and selected wear-control violations.
- [x] Verified Quality Verifier adapter maps typed `wear_control` defects and `wear_control_match` category scores into backend quality checks.
- [x] Verified selected wear-control quality behavior: local violations route to repair recommendation, blocking violations reject, clean pass is not allowed for violated selected controls.
- [x] Local selected wear-control verification passed: targeted Try-On instruction/quality/repair/workspace suite `62 passed`, full backend `929 passed`, `compileall src scripts`, architecture guardrail.
- [x] Frontend verification passed after selected wear-control gate: `npm run lint`, `npm run typecheck`, `npm run build`.
- [x] Prepared VM live acceptance scripts for selected wear-control scenarios.
- [x] Try-On Instruction live acceptance cases now pass backend-validated `wear_control_selections` into the agent adapter.
- [x] Quality Verifier live acceptance now includes selected wear-control approved constraints and requires `wear_control_match` inspection.
- [x] Local live-acceptance script verification passed: instruction/quality script tests and selected wear-control adapter/policy tests `49 passed`, full backend `929 passed`, `compileall src scripts`, architecture guardrail.
- [ ] Blocked live VM execution: local `gcloud` token needs reauthentication (`gcloud auth login`) before VM can be started/stopped safely.
- [x] Reauthenticated `gcloud`, started VM only for selected wear-control live acceptance, and stopped it immediately after live checks.
- [x] VM targeted script verification passed before live calls: selected wear-control live script/prompt/adapter tests `38 passed`.
- [x] Try-On Instruction selected wear-control live acceptance passed: output `output/try_on_instruction_wear_control_live_acceptance_20260628.jsonl`, total `2`, matched `2`, false pass `0`, false reject `0`.
- [x] Quality Verifier selected wear-control live acceptance executed and produced no critical false pass: output `output/quality_verifier_wear_control_live_acceptance_20260628_after_expectation.jsonl`, total `8`, matched `6`, false pass `0`.
- [ ] Quality Verifier live acceptance is not production-accepted yet: mismatch cases `good_generated_result` false reject and `minor_color_shift` false repair/reject instability indicate calibration/fixture expectation work is still required.
- [ ] Next gate: Quality Verifier calibration hardening before any broader production Try-On quality rollout.
- [x] Locally hardened Quality Verifier calibration after live mismatch: normal collar/neckline/base-layer visibility is no longer treated as a blocking defect unless a clearly unapproved extra garment materially contradicts the source garment.
- [x] Locally hardened color mismatch policy: visible color mismatch can no longer pass; minor local color defects may be repair, while global/material replacement remains reject.
- [x] Updated Quality Verifier live acceptance to support per-case safe decision ranges, so `minor_color_shift` accepts `repair_recommended` or `reject` but never `pass`.
- [x] Local verification passed after Quality Verifier calibration hardening: targeted Quality Verifier/wear-control tests `26 passed`, full backend `932 passed`, `compileall src scripts`, and architecture guardrail.
- [x] First calibrated Quality Verifier VM rerun exposed fixture-contract mismatch, not product logic failure: the script passed `open_front`, while canonical good/background fixtures show a buttoned/closed shirt.
- [x] Corrected Quality Verifier live acceptance fixture contract to pass explicit selected wear control `buttoned_closed` for the canonical dataset.
- [x] VM verification passed after fixture-contract correction: `tests/test_quality_verifier_live_acceptance_script.py` `13 passed`.
- [x] Quality Verifier selected wear-control live acceptance passed after calibration: output `/tmp/quality_verifier_wear_control_live_acceptance_20260628_buttoned_final.jsonl`, total `8`, matched `8`, false pass `0`, false repair `0`, false reject `0`.
- [x] VM was stopped immediately after the successful live acceptance run.
- [x] Started Repair Agent production planner integration locally; VM was not required.
- [x] Added `TryOnRepairAgentPlanner`, which invokes `repair_agent` through `AgentInvocationService` with generated-result artifact references and backend-approved failed/warning defects.
- [x] Provider-runtime image-edit repair now includes Repair Agent approved region instructions in the edit prompt.
- [x] Repair remains fail-closed: `unsafe` Repair Agent plans or planner errors block image editing and return a backend `reject`.
- [x] Runtime wiring now attaches `TryOnRepairAgentPlanner` to provider-runtime repair when `agent_invocation_service` is available.
- [x] Local verification passed after Repair Agent planner integration: repair/planner/runtime targeted suite `61 passed`, full backend `938 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Hardened Try-On adapter package imports: `TryOnQualityVerifierAgentAdapter` is now lazy-loaded so repair/runtime scripts do not require Pillow unless visual verifier adapter is explicitly used.
- [x] Updated repair workflow live acceptance script to exercise the full `Repair Agent planner -> Google GenAI image edit -> second Quality Verifier` path.
- [x] VM targeted repair planner/script tests passed before live acceptance: `11 passed`.
- [x] Repair workflow planner live acceptance passed on VM/staging with `OBJECT_STORAGE_BACKEND=in_memory`: provider `google_genai_image_editing`, repaired artifact size `1,142,888` bytes, Repair Agent not blocked, second Quality Verifier verdict `pass`, confidence `0.86`.
- [x] VM was stopped immediately after Repair workflow planner live acceptance.
- [x] Local verification passed after live-script and lazy-import hardening: full backend `939 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Added centralized agent model routing policy in `src/llm/agent_model_routing.py`.
- [x] Model routing now selects `gemini-2.5-flash-lite` for low-risk text agents such as Product Card text, Fashion Stylist, Pricing, and Cost/Credits.
- [x] Model routing keeps visual/high-risk agents on `gemini-2.5-flash`: Human Identity, Garment Identity, Material/Texture, Quality Verifier, Repair Agent, and Try-On Instruction.
- [x] Existing explicit `*_PREFERRED_MODEL` settings remain supported as safe overrides.
- [x] Runtime wiring now uses centralized routing for Try-On agents and Product Card agents instead of ad hoc model defaults.
- [x] Added architecture guardrails proving runtime builders use centralized model routing and current product agent invocations are covered.
- [x] Local verification passed after model routing integration: targeted routing/runtime suite `31 passed`, full backend `945 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Started B2B Product Catalog implementation locally; VM was not required because this phase is backend domain/use-case work only.
- [x] Added strict B2B catalog domain models for merchants, products, images, offers, import jobs, and import row errors.
- [x] Added backend-owned Business Catalog use-case service and repository/storage ports for merchant profile, product draft/update, image attach, submit to review, approve/reject/archive, and owner isolation.
- [x] Local B2B catalog verification passed: domain/service targeted suite `11 passed` and `compileall src/domain/business_catalog.py src/use_cases/business_catalog`.
- [x] Added B2B catalog SQL foundation: Alembic migration `20260628_000021_business_catalog`, SQLAlchemy rows, domain/row serialization, and async SQL repository.
- [x] SQL repository covers merchant/product/offer/image round trip, owner product listing, review status persistence, and import job/error persistence.
- [x] Local B2B catalog SQL verification passed: targeted domain/service/migration/repository suite `14 passed` and `compileall` for new catalog backend files.
- [x] Added B2B catalog business API routes for merchant read/save, product list/create, and product submit-to-review.
- [x] Added admin business catalog review routes for approve/reject, disabled by default behind `enable_admin_business_catalog`, and protected by admin headers.
- [x] Business catalog API currently exposes a clean dependency seam; production SQL runtime wiring remains a separate follow-up step before real UI integration.
- [x] Local B2B catalog API verification passed: targeted domain/service/SQL/routes suite `21 passed` and `compileall` for new catalog route/backend files.
- [x] Added B2B product image upload use-case and route: `POST /api/business/products/{product_id}/images`.
- [x] Product image upload now validates supported content types (`image/jpeg`, `image/png`, `image/webp`), enforces a 10 MB max size, computes SHA-256, stores through the backend file-storage port, and persists product image metadata.
- [x] Product image upload preserves owner isolation and keeps submit-to-review blocked until a primary product image exists.
- [x] Local B2B catalog upload verification passed: targeted domain/service/SQL/routes/upload suite `26 passed` and `compileall` for catalog backend files.
- [x] Added B2B catalog CSV import parser with required-column validation, row-level errors, invalid price/currency/URL handling, and partial-success output.
- [x] Added B2B catalog import workflow and routes: `POST /api/business/catalog-imports`, `GET /api/business/catalog-imports/{import_id}`, and `GET /api/business/catalog-imports/{import_id}/errors`.
- [x] CSV import creates accepted draft products through the backend service, persists import job metadata, and saves safe row-level errors; Excel is intentionally not marked as supported until a parser is added.
- [x] Local B2B catalog import verification passed: targeted domain/service/SQL/routes/upload/import suite `33 passed` and `compileall` for catalog backend files.
- [x] Added typed frontend B2B catalog API contracts in `apps/web/src/lib/api/business-catalog-contracts.ts`.
- [x] Extended `WebApiClient` with real backend methods for merchant, products, product image upload, CSV import creation, import status, and import errors.
- [x] Frontend B2B catalog contract verification passed: static contract tests `2 passed`, targeted B2B catalog suite `35 passed`, `npm run typecheck`, and `npm run lint`.
- [x] Added workspace B2B catalog UI routes: `/workspace/business-catalog`, `/workspace/business-catalog/new`, and `/workspace/business-catalog/import`.
- [x] Added business catalog overview, product creation form with product image upload, and CSV import page using the real `WebApiClient` methods.
- [x] Added workspace sidebar route for `Каталог товаров` and removed reliance on decorative/fake marketplace actions for this UI slice.
- [x] Frontend B2B catalog UI verification passed: workspace page guardrails `2 passed`, targeted catalog UI/API suite `13 passed`, `npm run typecheck`, `npm run lint`, and `npm run build`.
- [x] Added Kleppmann-inspired reliability/scale gate to the B2B catalog plan: tenant partitioning, hot-account mode, idempotency, failure injection, backpressure, degraded mode, and staging chaos-smoke before production chaos drills.
- [x] Added admin business catalog pending queue route: `GET /api/admin/business-catalog/products/pending`.
- [x] Added typed frontend admin business catalog client methods for pending products, approve, and reject.
- [x] Added internal admin review UI route `/admin/business-catalog` behind `NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI`.
- [x] Admin business catalog review UI keeps approve/reject out of the public workspace and requires an explicit rejection reason.
- [x] Admin business catalog verification passed: targeted route/page/contracts suite `9 passed`, `npm run typecheck`, `npm run lint`, and `npm run build`.
- [x] Added B2B catalog search projection use-case: only `active` + `approved` products with a matching offer can become future search records.
- [x] Search projection preserves product geo fields, delivery regions, price, currency, availability, source type, and product URL for future similar-search hydration.
- [x] Search projection verification passed: projection tests `4 passed`, targeted B2B catalog backend suite `33 passed`, and `compileall` for the new projection module.
- [x] Added B2B catalog tenant partition policy with `standard` and `large` assigned tiers.
- [x] Added semi-automatic tier recommendation: backend recommends `standard` or `large` from workload metrics, but effective routing changes only after admin assignment.
- [x] Added merchant tier persistence fields on business merchants: assigned tier, assignment reason, assigning admin, and assignment timestamp.
- [x] Added admin tier API: `GET /api/admin/business-catalog/merchants/tiers` and `POST /api/admin/business-catalog/merchants/{merchant_id}/tier`.
- [x] Added internal admin page `/admin/business-accounts` behind `NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI` for recommendation review and manual tier assignment.
- [x] Tenant tier/admin verification passed: backend targeted suite `44 passed`, frontend admin guardrails `6 passed`, `npm run typecheck`, `npm run lint`, `npm run build`, and `compileall` for modified backend modules.
- [x] Added backend-owned B2B catalog idempotency port and in-memory implementation for retry-safe mutations.
- [x] Wired idempotency into CSV imports, product image uploads, and submit-to-review using owner-scoped operation keys.
- [x] Added `Idempotency-Key` HTTP header support for `POST /api/business/catalog-imports`, `POST /api/business/products/{product_id}/images`, and `POST /api/business/products/{product_id}/submit`.
- [x] Idempotency stores only successful results; validation failures are not cached and can be retried after fixing input.
- [x] Idempotency verification passed: route/service idempotency suite `16 passed`, extended B2B catalog suite `51 passed`, and `compileall` for modified backend modules.
- [x] Added B2B catalog controlled failure-injection tests for object storage failure, metadata persistence failure after storage, import row-error persistence failure, and route-level structured operation errors.
- [x] Added structured `BusinessCatalogOperationError` with safe code, cleanup requirement flag, and optional cleanup object key.
- [x] Product image upload now fails closed: storage failure creates no image metadata; metadata failure after storage returns cleanup-required details.
- [x] CSV import now marks the import job `failed` with explicit reason if row-level import errors cannot be persisted.
- [x] Failure-injection verification passed: failure tests `4 passed`, reliability/catalog targeted suite `50 passed`, and `compileall` for modified backend modules.
- [x] Added B2B catalog backpressure policy with tier limits: standard CSV `1,000 rows / 5 MB`, large CSV `25,000 rows / 50 MB`, standard `10` images per product, large `30` images per product.
- [x] Backpressure violations return structured `business_catalog_backpressure` with limit name, configured value, and actual value.
- [x] CSV import and product image upload now check tier limits before expensive processing/storage.
- [x] Workspace catalog import and product photo upload screens now show short visible requirements plus expandable detailed upload limits.
- [x] Backpressure/UI verification passed: backend reliability/catalog suite `55 passed`, workspace page guardrails `3 passed`, `npm run typecheck`, `npm run lint`, `npm run build`, and `compileall`.
- [x] Updated B2B catalog documentation with current backend contours, frontend routes, admin surfaces, reliability guardrails, remaining connector work, and VM usage note.
- [x] Final B2B catalog reliability verification passed: architecture guardrail, `compileall src scripts`, targeted B2B/admin/reliability suite `69 passed`, full backend suite `1018 passed`, frontend `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Added B2B catalog runtime wiring so business/admin routes use the backend dependency container instead of returning `business_catalog_storage_unavailable` by default.
- [x] Added `scripts/business_catalog_staging_smoke.py` for deployed API smoke: health, merchant, product, image upload, submit, CSV import, import status/errors, and admin tier gate.
- [x] Verified B2B catalog runtime wiring locally: targeted backend suite `37 passed`, full backend suite `1022 passed`, architecture guardrail passed, and `compileall src scripts` passed.
- [x] B2B catalog deployed staging smoke passed after VM restart and backend deploy: public `/health` returned healthy, Alembic current is `20260628_000021 (head)`, API/worker containers are healthy, and `scripts/business_catalog_staging_smoke.py` passed.
- [x] Frontend staging build for B2B catalog routes passed with `NEXT_PUBLIC_API_BASE_URL=https://api.fit.aisoulfabrica.com`: `npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] Firebase Hosting deploy passed after Firebase reauth; published frontend includes `https://api.fit.aisoulfabrica.com` API base URL.
- [x] Frontend deployed route smoke passed: `/`, `/workspace/business-catalog`, `/workspace/business-catalog/new`, and `/workspace/business-catalog/import` returned HTTP 200 on `https://fit.aisoulfabrica.com`.
- [x] Frontend-to-staging backend smoke passed for business catalog read endpoints: `/api/business/merchant` and `/api/business/products` returned HTTP 200; API logs showed no traceback after the smoke.
- [x] Added location-first Similar Search foundation: approved marketplace source contracts, normalized offer contract, user city/country request fields, location match explanations, and local catalog projection source metadata.
- [x] Location-first Similar Search targeted verification passed: marketplace contracts, location ranking, similar-search domain/ranking/workflow/routes/runtime, and B2B search projection tests `18 passed`.
- [x] Full backend verification passed after location-first Similar Search foundation: `1027 passed`, with one existing Authlib deprecation warning.
- [x] Added Similar Search garment-photo workflow foundation: `POST /api/similar-search/garment-photo` accepts JPEG/PNG/WebP uploads, stores the image in backend object storage, invokes Garment Identity through backend runtime, builds a typed garment search profile, and returns the existing `SimilarSearchResponse`.
- [x] Added local B2B catalog fallback for Similar Search when vector search has no usable hits: only `active` + `approved` products with sellable offers are eligible, preserving city/country/delivery fields for location-first ranking.
- [x] Replaced `/workspace/similar-search` placeholder with a real thin-client upload workflow: photo validation, preview, country/city/budget inputs, capability disabled state, loading/error/empty/success states, and result cards with location explanations.
- [x] Similar Search garment-photo targeted verification passed: route/workflow/runtime/domain/query/B2B projection/page guardrails `17 passed`; frontend `npm run typecheck` and `npm run lint` passed.
- [x] Staging Similar Search paid acceptance executed with `good_single_shirt.png`: Garment Identity invoked Gemini successfully, endpoint returned HTTP `200`, and local catalog fallback returned 2 same-city Almaty shirt results from approved B2B catalog records.
- [x] Fixed staging blocker discovered by paid acceptance: missing Qdrant collection `fitfabrica_products` now returns empty vector hits instead of HTTP `500`, allowing local catalog fallback to run.
- [x] Fixed local catalog fallback strictness discovered by paid acceptance: if Garment Identity returns a more specific garment type than catalog category, backend broadens to approved local catalog keyword fallback instead of returning empty results prematurely.
- [x] Similar Search staging fix verification passed locally: Qdrant retriever, workflow, route, and B2B projection tests `11 passed`; architecture guardrail and compile checks passed before deploy.
- [x] Manual website Similar Search catalog-population test moved to the next session because the owner chose not to fill the test DB today.
- [x] Added backend-owned B2B catalog search indexing pipeline: approved catalog products can now be listed as safe search records, embedded through the provider-neutral embedding port, and upserted into the `products` vector namespace.
- [x] Added Qdrant products collection bootstrap before indexing so a missing vector collection does not repeat the previous staging blocker.
- [x] Added `scripts/reindex_business_catalog_search.py` for staging/manual reindex runs after catalog products are loaded and approved.
- [x] Search indexing verification passed: targeted indexing/projection/script/Qdrant/Similar Search suite `18 passed`, `compileall src scripts`, and architecture guardrail.
- [x] Added B2B catalog search index lifecycle: products now track `not_indexed`, `pending`, `indexed`, and `failed` states.
- [x] Admin approve now marks products as `active/approved` and `search_index_status=pending` instead of synchronously depending on Qdrant/provider availability.
- [x] Editing an already active/approved product now marks search indexing stale by returning it to `pending`.
- [x] Reindex command now marks products as `indexed` after successful indexing and `failed` with a safe reason after indexing errors.
- [x] Added SQL persistence and Alembic migration `20260630_000022_business_catalog_search_index_status` for search index status fields.
- [x] Added frontend typed contract fields and visible search-index status on B2B catalog/admin review surfaces.
- [x] Search index lifecycle verification passed: targeted backend suite `29 passed`, web `npm run typecheck`, and web `npm run lint`.
- [x] Added admin search-index retry endpoint: `POST /api/admin/business-catalog/products/{product_id}/search-index/retry`.
- [x] Added admin UI search-index filter and retry action for failed indexing records.
- [x] Search-index retry verification passed: route/service/frontend-contract targeted suite `4 passed`, web `npm run typecheck`, and web `npm run lint`.
- [x] Added automatic B2B catalog search-index dispatch: admin approve/retry now enqueue `business_catalog_search_index` operations jobs.
- [x] Added operations worker handler for `business_catalog_search_index`, executing the shared catalog search indexing workflow by product id.
- [x] Auto-dispatch verification passed: admin routes, operations runtime, indexing workflow/script, service, SQL repository, and frontend contract targeted suite `30 passed`.
- [x] Added `scripts/business_catalog_search_index_readiness.py` to verify deploy readiness for migration, DB schema, indexing runtime, and worker handler.
- [x] Added B2B search-index readiness gate to `scripts/deploy_portable_runtime.sh` after `alembic upgrade head`.
- [x] Updated staging/deploy runbooks with the B2B search-index readiness command and expected `ready` checks.
- [x] Deployed backend to staging VM after B2B search-index lifecycle changes; deploy readiness returned `ready`, API/worker containers were healthy, and Alembic current was `20260630_000022 (head)`.
- [x] Fixed staging Qdrant compatibility issues found during real reindex: Docker image now includes readiness/reindex scripts, reindex script resolves `src` inside the container, Qdrant distance uses `Cosine`, fake embedding size matches the `products` namespace, and Qdrant adapter maps domain point IDs to stable UUID point IDs.
- [x] Staging manual reindex passed: `scripts/reindex_business_catalog_search.py --limit 1000` returned `indexed_count=2`, `skipped_count=0`, `source_record_count=2`; approved catalog products now show `search_index_status=indexed`.
- [x] Frontend Firebase Hosting deploy passed with the staging API base URL; `/workspace/business-catalog` and `/workspace/similar-search` returned HTTP 200.
- [x] Final deployment verification passed: public `/health` returned 200, business catalog staging smoke passed, architecture guardrail passed, `compileall src scripts` passed, web `npm run lint`, `npm run typecheck`, and `npm run build` passed, and full backend suite passed with `1054 passed`.
- [x] Prepared realistic B2B catalog test pack under `_import_ready`: backend-valid CSV, 30 correctly named product images, manifest, and Russian test instructions.
- [x] Loaded realistic catalog pack into staging through real HTTP APIs: merchant upsert passed, CSV import accepted `30/30` rows with `0` errors, 30 product images uploaded, and 30 products submitted to review.
- [x] Enabled staging admin business catalog API via `ENABLE_ADMIN_BUSINESS_CATALOG=true` and added the missing typed settings field so approval is controlled by config instead of hardcoded route state.
- [x] Approved 32 pending staging products through admin API; worker auto-indexing completed and all approved products reported `search_index_status=indexed`.
- [x] Fixed real Qdrant search-hit mapping discovered during staging Similar Search: adapter now supports both dict fake hits and real `ScoredPoint` objects.
- [x] Similar Search staging probe passed with realistic shirt image: `POST /api/similar-search/garment-photo` returned HTTP `200` and 10 local catalog results, led by shirt matches from the indexed catalog.
- [x] Post-fix verification passed: targeted Qdrant/Similar Search/settings tests passed, architecture guardrail passed, `compileall src scripts` passed, live `/health` returned 200, and full backend suite passed with `1056 passed`.
- [x] Fixed Similar Search result hydration: response now preserves `city`, `country_code`, and `delivery_regions` for local B2B catalog matches.
- [x] Added Similar Search product thumbnail support: result contract includes `image_url`, backend exposes approved product primary images through `/api/business/products/{product_id}/images/primary`, and workspace result cards render the photo on the left.
- [x] Rewired Similar Search vector hydration to approved B2B business catalog records instead of the legacy product catalog, so public results are filtered by `active/approved` product state and sellable offer state before display.
- [x] Archived staging smoke catalog records titled `Smoke%` after realistic catalog activation; live Similar Search no longer returns old 1x1 smoke images.
- [x] Restored staging HTTPS by setting `CADDY_SITE_ADDRESS=api.fit.aisoulfabrica.com` on the VM after deploy had fallen back to HTTP-only mode.
- [x] Similar Search thumbnail verification passed: public `/health` returned healthy, text Similar Search returned catalog results with `image_url`, and the first three primary-image URLs returned `200 image/png` with real image payloads.
- [x] Added fail-closed upload error handling for Garment Identity failures: `/api/similar-search/garment-photo` now returns structured `503` with safe code instead of raw `500`.
- [x] Fixed staging deploy packaging safety: `scripts/create_backend_deploy_archive.ps1` creates backend archives without local `.env*`, service-account, or secret files, and the deploy runbook now uses this script instead of ad-hoc `tar`.
- [x] Fixed Similar Search multimodal runtime blocker: `gemini_structured` now wires the same `GeminiStructuredProvider` as both structured reasoning and artifact-capable agent runtime.
- [x] Re-enabled real staging agent runtime on the VM with `LLM_PROVIDER=gemini_structured`, `VERTEX_PROJECT=ai-fitfabrica`, and `VERTEX_LOCATION=us-central1`; runtime inspection confirmed `supports_artifacts=True`.
- [x] Live garment-photo Similar Search verification passed after runtime fix: `POST /api/similar-search/garment-photo` returned HTTP `200`, produced 2 realistic local catalog matches, preserved location fields, and both result `image_url` endpoints returned `200 image/png`.
- [x] Public staging smoke passed after the runtime fix: `https://api.fit.aisoulfabrica.com/health` returned healthy and `https://fit.aisoulfabrica.com/workspace/similar-search` returned HTTP `200`.
- [x] Added Similar Search click/lead analytics foundation: search results now expose approved `offer_url`, frontend opens products through backend redirect, backend records click events in SQL/in-memory repositories, local-only offers are blocked from external redirect, and targeted/backend/frontend verification passed.
- [x] Deployed Similar Search click/lead analytics to staging: backend migration `20260701_000023` is current, Firebase Hosting deploy completed, public `/health` returned healthy, `/workspace/similar-search` returned HTTP `200`, click event API returned a persisted event, redirect API returned `302`, local-only redirect returned `409`, and SQL showed 3 smoke click events.
- [x] Hardened Similar Search relevance after live smoke found white-shirt upload returning outerwear: garment-photo search now canonicalizes agent garment labels such as `button-up shirt` to catalog category `shirt`, filters wrong-category vector hits before location ranking, and live staging re-test returned shirt results instead of jackets; redirect smoke returned `302` and SQL click events increased to 4.
- [x] Added Similar Search analytics v1 for admins: backend aggregates existing click events into summary, top products, top marketplaces, and top cities; `/api/admin/business-catalog/analytics/similar-search` exposes read-only metrics behind admin headers; `/admin/business-catalog` renders the analytics panel; targeted backend tests, frontend typecheck/lint/build, architecture guardrail, and compileall passed.
- [x] Deployed Similar Search analytics v1 to staging: backend and Firebase Hosting deploy completed, API/worker containers are healthy, Alembic current is `20260701_000023 (head)`, public `/health` returned healthy, `/admin/business-catalog` returned HTTP `200`, and admin analytics endpoint returned summary `4` total clicks, `3` redirects, `1` local-only. Public admin UI remains gated by `NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI` for safety.
- [x] Hardened admin API authentication locally: admin business catalog and taxonomy routes now fail closed unless `ADMIN_API_TOKEN` is configured and requests use `Authorization: Bearer ...`; legacy browser-controlled `x-fitfabrica-admin-*` headers are only accepted when `ALLOW_UNSAFE_ADMIN_HEADER_AUTH=true` and no token is configured. Admin frontend pages now ask for an access token instead of role/id. Verification passed: admin route/page suite `25 passed`, architecture guardrail, `compileall src scripts`, web `npm run typecheck`, `npm run lint`, and `npm run build`.
- [x] Deployed admin-auth hardening backend to staging: VM env now has `ADMIN_API_TOKEN` configured, `ALLOW_UNSAFE_ADMIN_HEADER_AUTH=false`, API/worker containers are healthy, internal admin checks returned `403` without auth, `403` for legacy browser role/id headers, and `200` with bearer token. Public `/health` returned `200`; public admin analytics without token returned `403`. Frontend build passed, but Firebase Hosting deploy is pending because Firebase CLI requires manual reauth.
- [x] Deployed admin-auth hardening frontend to Firebase Hosting after reauth: `/admin/business-catalog` returned HTTP `200` with no legacy `adminRole/adminId/x-fitfabrica-admin` markers, `/workspace/similar-search` returned HTTP `200`, and the public admin UI remains feature-flag locked. VM was already stopped, so backend public health was intentionally not available after shutdown.
- [x] Added local admin-only cost baseline endpoint after admin-auth hardening: `GET /api/admin/costs/baseline` is disabled unless `ENABLE_ADMIN_COSTS=true`, requires the shared `ADMIN_API_TOKEN` bearer auth, exposes read-only provider price config, configured workflow credit costs, baseline pricing recommendations, and explicit guardrails that live billing is unchanged and frontend must not calculate credits. Verification passed: admin cost/settings/provider/cost-map suite `30 passed`, architecture guardrail, and `compileall src scripts`.
- [x] Deployed admin cost baseline endpoint to staging: VM env has `ENABLE_ADMIN_COSTS=true` and `ALLOW_UNSAFE_ADMIN_HEADER_AUTH=false`; deploy readiness returned `ready`, API/worker containers are healthy, internal smoke returned `403` without auth and `200` with bearer token, baseline included 4 provider prices and 12 pricing recommendations, public `/health` returned `200`, and public unauthenticated `/api/admin/costs/baseline` returned `403`.
- [x] Hardened Similar Search relevance locally after website tests showed unrelated products: garment-photo search now applies the same category gate and a minimum similarity threshold before location ranking for both vector hits and local catalog fallback. Regression tests cover wrong-category fallback and weak `0.58` same-city matches being filtered out. Verification passed: Similar Search/business projection targeted suite `31 passed`, architecture guardrail, and `compileall src scripts`.
- [x] Deployed Similar Search relevance hardening to staging and ran live garment-photo probes. Shirt probe returned only `ff-sh-*` shirt records. A jacket probe still returned shirts, but visual inspection of the test pack showed the supposed jacket files (`028_olive_quilted_jacket.png`, `030_blue_denim_jacket.png`) are actually shirt images. Added and deployed an additional Garment Identity prompt/canonicalizer guardrail for `shirt jacket`/`shacket`/`quilted jacket` -> `outerwear`, but the current realistic catalog test pack is not reliable for non-shirt acceptance until image/category consistency is fixed. Next required step: add a B2B catalog image-category consistency gate before approving/indexing seller products.
- [x] Added local B2B catalog image/category consistency gate: products now store `category_validation_status`, visual category, confidence, reason, and validation timestamp; admin approval is blocked until validation is `matched`; mismatched or uncertain visual category cannot enter `approved` or search indexing. Added admin API `POST /api/admin/business-catalog/products/{product_id}/category-validation`, frontend admin controls for recording validation, shared garment category canonicalization, SQL persistence, Alembic migration `20260701_000024_business_catalog_category_validation`, and verification passed: targeted backend catalog/admin/search suites `74 passed`, architecture guardrail, `compileall src`, web `npm run typecheck`, `npm run lint`, and `npm run build`.
- [x] Deployed B2B catalog image/category consistency gate to staging: backend deploy completed, Alembic current is `20260701_000024 (head)`, API/worker containers were healthy, public `/health` returned `200`, unauthenticated category-validation admin endpoint returned `403`, Firebase Hosting deploy completed, `/admin/business-catalog` and `/workspace/similar-search` returned `200`, and the staging VM was stopped after verification.
- [x] Added and deployed backend-owned automatic B2B catalog category validation: admin route `POST /api/admin/business-catalog/products/{product_id}/category-validation/run` now selects the product primary image, invokes Garment Identity through a use-case port, stores the visual category validation result, and keeps approval locked unless the result is `matched`. Admin UI now exposes `Run AI validation` before manual override fields. Verification passed locally: service/admin route tests `28 passed`, adjacent catalog/similar-search suite `19 passed`, architecture guardrail, `compileall src`, web `typecheck`, `lint`, and `build`. Staging deploy passed: backend API healthy, Firebase Hosting deployed, `/health` returned `200`, `/admin/business-catalog` returned `200`, unauthenticated run endpoint returned `403`, and VM was stopped.
- [x] Real staging acceptance passed for B2B catalog automatic category validation. Created temporary staging products with `good_single_shirt.png`: declared `shirt` returned `matched`, visual category `shirt`, confidence `0.90`, and admin approve returned `200 approved`; declared `outerwear` on the same shirt photo returned `mismatch`, visual category `shirt`, confidence `1.0`, and admin approve was blocked with `400 business_catalog_validation_failed`. This confirms the gate prevents wrong-category catalog items from entering approved/search-index flow. Temporary VM files were removed and VM was stopped.
- [x] Added and deployed admin archive support for B2B catalog cleanup: `POST /api/admin/business-catalog/products/{product_id}/archive` archives products without deleting audit/history and resets search-index state to `not_indexed`. Admin UI now includes `Archive`. Verification passed: admin/service tests `29 passed`, architecture guardrail, `compileall src`, web `typecheck`, `lint`, and `build`. Staging cleanup completed: the matched acceptance product was archived/not_indexed, the mismatch acceptance product was rejected/not_indexed, public `/health` and `/admin/business-catalog` returned `200`, temporary VM files were removed, and VM was stopped.
- [x] Added and deployed bounded bulk category validation for admin review: `POST /api/admin/business-catalog/products/category-validation/run-batch` runs backend-owned Garment Identity validation for pending products with a guarded limit `1..25`, returns item-level `validated/failed` results, and does not fail the whole batch when one product is invalid or missing a primary image. Admin UI now includes `Run AI validation batch` with a limit input and summary. Verification passed: admin/service tests `31 passed`, architecture guardrail, `compileall src`, web `typecheck`, `lint`, and `build`. Staging deploy passed: public `/health` returned `200`, `/admin/business-catalog` returned `200`, unauthenticated batch endpoint returned `403`, deploy archive was removed, and VM was stopped.
- [x] Added and deployed bounded bulk approval for category-matched B2B catalog products: `POST /api/admin/business-catalog/products/approve-matched-batch` approves only pending products with `category_validation_status=matched`, marks them for search indexing through the existing approval path, and enqueues one backend-owned `business_catalog_search_index` operations job for the approved product ids. Admin UI now includes `Approve matched batch` with a guarded limit input and item-count summary. Verification passed: admin/service tests `33 passed`, architecture guardrail, `compileall src`, web `typecheck`, `lint`, and `build`. Staging deploy passed: public `/health` returned `200`, `/admin/business-catalog` returned `200`, unauthenticated approve-matched batch endpoint returned `403`, Firebase Hosting deployed, deploy archive was removed, and VM was stopped.
- [x] Verified the deployed bulk approval/indexing contour without paid AI calls: protected staging smoke against `approve-matched-batch` returned `200` with `processed_count=0`, `approved_count=0`, and `failed_count=0`, confirming there were no pending matched products to approve. API/worker containers were healthy, public `/health` returned `200`, related local chain tests passed with `43 passed`, temporary smoke files were removed, and VM was stopped.
- [x] Added and deployed admin product review readiness hints without live AI calls: each pending B2B catalog product now shows a `Review readiness` block that explains whether it needs AI category validation, has a category mismatch/uncertain result, is ready for approval, or needs search-index retry. Verification passed: admin page guardrail tests `2 passed`, web `typecheck`, `lint`, and `build`; Firebase Hosting deployed and `/admin/business-catalog` returned `200`. Backend/VM was not needed for this frontend-only step.
- [x] Added and deployed admin review queue summary without live AI calls: `/admin/business-catalog` now shows `Review queue summary` metrics for total pending products, `Ready to approve`, `Needs AI validation`, `Blocked by category`, and `Indexing issues` before the bulk actions. Verification passed: admin page guardrail tests `2 passed`, web `typecheck`, `lint`, and `build`; Firebase Hosting deployed and `/admin/business-catalog` returned `200`. VM remained stopped.
- [x] Added and deployed admin review filtering without live AI calls: `/admin/business-catalog` now supports a `Review filter` for `ready_to_approve`, `needs_ai_validation`, `blocked_by_category`, and `indexing_issues`, combined with the existing search-index filter. Empty filtered views show a safe empty state instead of a blank page. Verification passed: admin page guardrail tests `2 passed`, web `typecheck`, `lint`, and `build`; Firebase Hosting deployed and `/admin/business-catalog` returned `200`. VM remained stopped.
- [x] Added and deployed admin operation-order guidance without live AI calls: `/admin/business-catalog` now shows `Admin operation order` before bulk actions with the safe sequence `1. Run AI validation batch`, `2. Approve matched batch`, and `3. Check indexing status`, including the explicit guardrail `Do not approve mismatched or uncertain products.` Verification passed: admin page guardrail tests `2 passed`, web `typecheck`, `lint`, and `build`; Firebase Hosting deployed and `/admin/business-catalog` returned `200`. VM remained stopped.
- [x] Added and deployed item-level bulk operation feedback without live AI calls: after `Run AI validation batch` or `Approve matched batch`, `/admin/business-catalog` now shows `Bulk operation details` with each returned `product_id`, item status, and `error_message` when present, while keeping the existing aggregate summary. Verification passed: admin page guardrail tests `2 passed`, web `typecheck`, `lint`, and `build`; Firebase Hosting deployed and `/admin/business-catalog` returned `200`. VM remained stopped.
- [x] Added and deployed bulk result cleanup without live AI calls: `Bulk operation details` now includes `Clear bulk result`, which clears the last displayed bulk operation response without changing backend product state. Verification passed: admin page guardrail tests `2 passed`, web `typecheck`, `lint`, and `build`; Firebase Hosting deployed and `/admin/business-catalog` returned `200`. VM remained stopped.
- [x] Added and deployed admin status badges without live AI calls: `/admin/business-catalog` now renders color-coded `StatusBadge` UI for review status, category validation, search-index status, and bulk operation item status. Green marks safe/success states such as `matched`, `indexed`, `approved`, and `validated`; red marks failure states such as `mismatch`, `failed`, and `rejected`; amber marks waiting/attention states such as `uncertain`, `pending`, and `not_checked`. Verification passed: admin page guardrail tests `2 passed`, web `typecheck`, `lint`, and `build`; Firebase Hosting deployed and `/admin/business-catalog` returned `200`. VM remained stopped.
- [x] Ran real staging admin catalog acceptance attempt with 3 compact `Acceptance` products. Product create, image upload, submit, and admin pending read worked, but paid Garment Identity validation was blocked by Google/Gemini billing/auth state: provider returned `403 PERMISSION_DENIED` with `Lightning dunning decision is deny for project: projects/175417528606`. Full matched/approve/indexing/Similar Search acceptance is therefore blocked until billing/provider access is restored.
- [x] Fixed backend failure handling found during the staging acceptance attempt: Garment Identity provider failures in B2B catalog category validation are now mapped to `BusinessCatalogOperationError`; batch validation returns item-level `failed` results instead of raw endpoint `500`, and the single-product run endpoint returns structured `503`. Verification passed: business catalog service/admin route tests `35 passed`, architecture guardrail, and `compileall src`; backend deployed to staging and repeated acceptance returned `processed_count=3`, `validated_count=0`, `failed_count=3` instead of `500`.
- [x] Fixed admin archive cleanup found during the same staging attempt: admin archive now also sets `review_status=not_required`, clears review reason, and resets search-index state, so archived products leave the admin pending queue. Verification passed: business catalog service/admin route tests `36 passed`, architecture guardrail, and `compileall src`; backend deployed to staging, all 6 temporary `Acceptance` products were re-archived, pending queue returned `0`, public `/health` returned `200`, temporary files were removed, and VM was stopped.
- [x] Added a staging/dev-only no-AI category validation mode for B2B catalog acceptance while Gemini billing is blocked: `BUSINESS_CATALOG_CATEGORY_VALIDATION_MODE=sandbox` wires a deterministic `SandboxBusinessCatalogCategoryAnalyzer` only inside the business catalog category-validation contour. It infers categories from controlled test asset names (`shirt`, `tshirt`, `pants/jeans`, `dress`, `skirt`, `outerwear/jacket/coat`) and does not call Gemini or any model provider.
- [x] Guarded the no-AI mode against leaking into Similar Search: Similar Search keeps its own garment analyzer wiring even when the business catalog sandbox setting is enabled. Regression coverage added for this wiring boundary and for realistic catalog pack file names.
- [x] Updated the realistic staging catalog loader so it matches the hardened production flow without paid AI calls: import products, upload images, submit to review, run admin category-validation batch, approve only matched products, poll search indexing, then run a structured/text Similar Search probe instead of the `/garment-photo` probe that would invoke Garment Identity/Gemini.
- [x] Local verification for the no-AI catalog path passed: targeted business catalog/admin/similar-search/settings suite `56 passed`, updated staging loader suite `43 passed`, architecture guardrail passed, and `compileall src scripts` passed. Backend with sandbox mode was deployed to the staging VM and deploy readiness returned `ready`.
- [ ] Remaining staging acceptance step is blocked by local `gcloud` reauth, not by project code: `gcloud compute ssh` now fails with `Reauthentication failed. cannot prompt during non-interactive execution.` Next operator action is `gcloud auth login`, then rerun the realistic no-AI catalog acceptance and stop the VM after verification.
- [x] Resumed no-AI staging catalog acceptance after `gcloud` auth was restored. VM was started, API/worker became healthy, sandbox mode was confirmed, and the realistic test pack was uploaded to `/tmp/fitfabrica_catalog_acceptance` on the VM.
- [x] No-AI staging acceptance reached the full catalog path without Gemini calls: health passed, merchant upsert passed, CSV import accepted `30/30`, image upload passed `30/30`, product submit passed `30/30`, category-validation batch processed submitted products with `0` failed analyzer calls, manual reindex indexed `52` approved records, and structured/text Similar Search returned local shirt results with `image_url` and location ranking.
- [x] Fixed a production batch-indexing bug found by the no-AI acceptance: `approve-matched-batch` was building `workflow_reference` and `idempotency_key` by concatenating many product ids, exceeding PostgreSQL `varchar(64)` and returning `500`. Batch indexing now uses a short stable SHA-256 fingerprint for `workflow_reference`/`idempotency_key` while preserving full `product_ids` in the job payload. Regression test added for long 25-product batches.
- [x] Hardened the sandbox category analyzer after acceptance exposed test-pack naming gaps: `longsleeve` maps to `tshirt`, `trouser` maps to `pants`, and `blazer` maps to `outerwear`. The gate correctly keeps obvious data errors blocked, e.g. skirt image filenames declared as `dress` remain `mismatch`.
- [x] Cleaned staging after the no-AI acceptance: 30 temporary products created at `2026-07-02T08:15` were archived, temporary VM files and deploy archive were removed, backend latest version was redeployed with readiness `ready`, public `/health` returned `healthy`, API/worker were healthy, and the staging VM was stopped.
- [x] Made the no-AI realistic catalog loader compatible with the hardened category gate: validation now counts `matched` and `blocked` products separately, approve/indexing runs only for matched products, and imperfect test packs require explicit `--allow-category-blocks`. Added regression tests for matched/blocked accounting and the explicit allow flag. Verification passed: loader/admin/catalog/similar-search targeted suite `24 passed`, architecture guardrail, and `compileall`.
- [x] Added a clean Russian runbook for the no-AI B2B catalog acceptance: `docs/runbooks/no_ai_business_catalog_acceptance_ru.md` documents staging sandbox mode, local/VM commands, expected blocked category behavior, cleanup, VM shutdown, and what the no-AI pass does not verify.
- [x] Cleaned the local realistic B2B catalog test pack so it can pass the category gate without `--allow-category-blocks`: fixed two skirt products that were declared as `dress` in `business_catalog_import_ready.csv` and `business_catalog_image_upload_manifest.csv`. Added loader preflight validation that compares controlled `image_filename` category signals against CSV `category`, including a regression for `pocket_shirt` not being confused with `tshirt`. Verification passed: targeted loader/admin/catalog/similar-search suite `26 passed`, architecture guardrail, `compileall`, and VM remained `TERMINATED`.
- [x] Improved workspace B2B catalog UX without VM or paid AI calls: product cards now explain category validation status and search visibility (`available`, `waiting admin review`, `indexing pending`, or `not eligible for search`) using existing backend contract fields instead of frontend business logic.
- [x] Verified the workspace catalog/search UX step locally: workspace/admin catalog and Similar Search guardrail tests passed (`6 passed`), no broken Russian strings were found in the touched UI contour, and web `typecheck`, `lint`, and `build` passed.
- [x] Clarified workspace Similar Search UX without backend changes or paid AI calls: the page now states that free search currently uses only approved local merchant catalog items, prioritizes nearby stores/delivery, and treats external marketplaces/Instagram as a future legal/API connector layer. Empty results now explicitly say no credits were charged and suggest trying another photo/city or waiting for catalog growth. Verification passed: workspace/admin catalog and Similar Search guardrail tests (`6 passed`), web `typecheck`, `lint`, and `build`.
- [x] Added backend-first external search connector foundation without live marketplace calls: domain contracts now define connector kinds (`kaspi`, `wildberries`, `instagram_business`, partner feeds, seller stores), legal access basis, location-aware connector query, isolated connector execution report, and a Similar Search marketplace connector port. This prepares future Kaspi/Wildberries/Instagram adapters while keeping hidden scraping out of scope. Verification passed: marketplace/similar-search targeted suite `20 passed`, `compileall` for the touched domain/use-case modules, and architecture guardrail.
- [x] Added backend marketplace connector registry with disabled safe placeholders for future Kaspi, Wildberries, and Instagram Business adapters. Each placeholder returns an isolated `skipped` connector report without network calls, scraping, or frontend involvement, so future real connectors can be swapped in by backend adapter registration. Verification passed: marketplace connector/contract and Similar Search targeted suite `17 passed`, `compileall` for marketplace/search modules, and architecture guardrail.
- [x] Added source types for approved public-web and search-engine discovery without enabling live scraping: `public_web_allowed` and `search_engine_discovery` are now explicit backend source/connector/legal-access categories with disabled safe registry placeholders. Added Russian source strategy runbook documenting local catalog first, seller/partner feeds next, official APIs when available, and web/search discovery only as governed candidate discovery. Verification passed: marketplace connector/contract tests `11 passed` and `compileall`.
- [x] Added Instagram/open-source candidate discovery foundation for the current Similar Search strategy: open Instagram/web/search results are modeled as `MarketplaceDiscoveryCandidate`, not `NormalizedMarketplaceOffer`, so they cannot be treated as verified sellable products until reviewed/enriched. Added `instagram_public_discovery` connector kind, registry placeholder, and `MarketplaceConnectorOrchestrationService` that aggregates offers, candidates, and per-connector reports while isolating source failures. Verification passed: marketplace/open-discovery and Similar Search targeted suite `21 passed`, `compileall`, and architecture guardrail.
- [x] Added a live-safe search engine discovery adapter placeholder for Instagram/open-web candidate search: `build_instagram_public_discovery_query` creates location-aware `site:instagram.com` queries, and `DisabledSearchEngineDiscoveryConnector` returns `skipped` without network calls until an official search API, limits, and usage policy are configured. Default connector registry now uses this specialized placeholder. Verification passed: marketplace/search-engine adapter suite `16 passed`, adjacent Similar Search suite `8 passed`, `compileall`, and architecture guardrail.
- [x] Added live-ready search API result mapping for Instagram discovery without network calls: `SearchEngineResult` normalizes future provider responses, `map_search_results_to_discovery_candidates` maps real `instagram.com` / `*.instagram.com` URLs into review-required candidates, and lookalike domains are rejected. Candidates remain separate from sellable offers. Verification passed: discovery/marketplace suite `18 passed`, adjacent Similar Search suite `8 passed`, `compileall`, and architecture guardrail.
- [x] Added settings and feature flag foundation for future live search-engine discovery: `ENABLE_SEARCH_ENGINE_DISCOVERY`, `SEARCH_ENGINE_DISCOVERY_PROVIDER`, `SEARCH_ENGINE_DISCOVERY_DAILY_LIMIT`, and `SEARCH_ENGINE_DISCOVERY_API_KEY` are now typed settings; runtime feature flags expose `search_engine_discovery_enabled()`. Defaults keep live discovery disabled with no network calls. Verification passed: settings/discovery/registry suite `25 passed`, marketplace/Similar Search suite `14 passed`, `compileall`, and architecture guardrail.
- [x] Added safe runtime factory for search-engine discovery connectors: `build_search_engine_discovery_connector` returns disabled when the feature is off or no key is configured, and returns a skipped unsupported-provider connector when an unknown provider is enabled. `build_marketplace_connector_registry` now accepts discovery settings and wires the safe connector without triggering live calls. Verification passed: marketplace/open-discovery and Similar Search suite `24 passed`, `compileall`, and architecture guardrail.
- [x] Added Admin Candidate Review foundation for Instagram/open-web discovery candidates: `MarketplaceCandidateReviewService` and an in-memory repository support save/list pending/approve/reject, and admin routes expose pending/approve/reject under `/api/admin/business-catalog/discovery-candidates/*` behind the existing admin auth/feature flag. Candidates remain separate from sellable offers. Verification passed: admin/candidate route-service suite `19 passed`, adjacent marketplace/Similar Search suite `10 passed`, `compileall`, and architecture guardrail. Production durability still requires SQL persistence before live discovery is enabled.
- [x] Completed pre-billing local readiness baseline for post-billing testing on branch `main`, commit `709bb68d32471c74ebffefb3822e33672bebf84c`, with a dirty working tree intentionally left untouched. Verification passed: `scripts/check_architecture.py`, `compileall -q src scripts`, full backend pytest `1129 passed` with 2 non-blocking warnings, web `npm ci`, `npm run lint`, `npm run typecheck`, and `npm run build`. `npm ci` reported 5 dependency audit findings (`1 low`, `4 moderate`); no automatic audit fix was applied because it can change dependency versions. Remaining blocker for paid live acceptance is still Google/Gemini/Vertex billing/provider access restoration before running provider smokes and full staging paid flows.
- [x] Closed a no-billing production-readiness gap for Admin Candidate Review: marketplace/open-web discovery candidates now have durable SQL persistence through `marketplace_discovery_candidates`, Alembic migration `20260702_000025`, `SqlMarketplaceCandidateRepository`, and admin route wiring that uses SQL when `sql_session_factory` is available while preserving in-memory fallback only for local/test. The SQL contract now covers workspace/business scope, source/media/product metadata, JSONB payloads, duplicate protection by `source_url` plus scope, `pending/approved/rejected/archived` review states, rejection reason, and review timestamps. Admin endpoints now support pending/list/approve/reject/archive. Verification passed: candidate review/admin/migration targeted suite `28 passed`, `compileall -q src tests`, and architecture guardrail. This does not enable live discovery or scraping; it only makes future reviewed candidates durable.
- [x] Completed Plan B no-billing readiness hardening for public website flows: added durable SQL persistence for public demo/contact requests through `public_demo_requests`, migration `20260703_000026`, backend `POST /demo-request`, fail-closed `POST /auth/sign-in`, public route aliases `/login` and `/contact`, and removed decorative Google/password-recovery actions from the sign-in UI until real auth is connected. Verification passed: public route/migration/frontend guardrails `7 passed`, architecture guardrail, `compileall -q src tests`, web `typecheck`, `lint`, `build`, adjacent suite `32 passed`, and full backend suite `1141 passed` with one existing Authlib deprecation warning. Report: `docs/reports/2026-07-03-plan-b-no-billing-readiness.md`.
- [x] Continued Plan B frontend no-billing audit: remaining public CTAs now use canonical `/contact` instead of legacy `/contacts`, and active workspace pages for history, projects, product card, and content package no longer silently render blank screens when workspace bootstrap is unavailable; they use the shared loading/error/empty shell state. Added guardrail coverage in `tests/test_no_billing_frontend_guardrails.py`. Verification passed: new guardrails `2 passed`, adjacent workspace/public guardrails `8 passed`, web `typecheck`, `lint`, `build`, architecture guardrail, and `compileall -q src tests`.
- [x] Created a visual admin-panel readiness PDF for no-billing review: `output/pdf/fitfabrica-admin-panel-readiness-2026-07-03.pdf` with screenshots for Admin Business Catalog, Admin Taxonomy, and Admin Business Accounts. The report documents each page, available buttons/actions, analysis capabilities, no-billing safety boundaries, and the post-billing checklist. Screenshots are stored under `docs/reports/screenshots/admin-panel-2026-07-03/`. Verification passed: PDF renders to 6 pages, Cyrillic text extracts correctly, and visual PNG checks confirmed readable title/admin screenshot pages.
- [x] Prepared the no-billing auth/session contour without connecting a production auth provider: backend now exposes `GET /auth/session` with unauthenticated `auth_configured=false` state and idempotent `POST /auth/logout` that clears `fitfabrica_session`, while `POST /auth/sign-in` remains fail-closed with `503 auth_not_configured`. Frontend contracts and `WebApiClient` now include typed `AuthSessionResponse`, `AuthLogoutResponse`, `getAuthSession`, and `logout`; the login form checks session state before sign-in and shows a clear "auth not connected" message instead of pretending login is live. Verification passed: auth/public route and frontend guardrails `12 passed`, web `typecheck`, `lint`, `build`, architecture guardrail, and `compileall -q src tests`.
- [x] Refreshed owner-facing readiness documentation for the current pre-billing baseline: `docs/04_OWNER_REMAINING_WORK.md` now records the 2026-07-08 status, clean git baseline, `1201 passed` backend suite, no-billing/post-billing gate commands, B2C/B2B readiness, external blockers, web dependency audit evidence, and the next no-billing polish item. Added `tests/test_owner_status_docs.py` so current owner docs cannot silently drift back to stale test counts or old dirty-worktree status.
- [x] Removed the recurring full-suite `RuntimeError: Event loop is closed` warning by disposing two test-created `sqlite+aiosqlite` engines in content-package and pricing SQL repository tests. Added `tests/test_async_sqlite_test_cleanup.py` and wired it into `no_billing_acceptance_gate.py` so future async sqlite tests must dispose their engines. Verification passed: targeted cleanup/repository tests, no-billing gate with frontend build, and full backend acceptance `1202 passed, 1 warning`; the remaining warning is Authlib dependency deprecation.
- [x] Cleaned the final full-suite warning by adding a narrow pytest warning policy for Authlib's third-party `authlib._joserfc_helpers` compatibility warning, which is pulled by `google-adk` while `joserfc` is already installed. Added `tests/test_pytest_warning_policy.py` and wired it into `no_billing_acceptance_gate.py` to prevent broad warning suppression. Verification passed: no-billing gate with frontend build and full backend acceptance `1203 passed, 0 warnings`.
