# Human Identity Policy Hardening Report

Date: 2026-06-16

## Verdict

Human Identity backend policy hardening is implemented and deployed to staging.

Production policy acceptance: passed.

Full live provider rerun: partially limited by Gemini `429 RESOURCE_EXHAUSTED`; the backend policy was therefore also verified inside the rebuilt staging API container with deterministic v2 facts from the acceptance cases.

## Contract Changes

`HumanIdentityContract` and persisted Try-On human analysis now include:

- `subject_count`
- `crop_quality`
- `try_on_body_coverage`
- `occlusion_risk`
- `required_regions_missing`

Contract version: `human_identity.contract.v2`.

## Backend Policy Rules

Normal Try-On now blocks when:

- no human subject is detected;
- more than one subject is detected;
- face is not fully visible;
- required body regions are missing;
- crop is headshot or extreme crop;
- Try-On body coverage is insufficient;
- occlusion risk is high;
- confidence is below the backend threshold;
- uncertainty is high.

`preservation_targets` remains useful structured metadata, but it is no longer a hard blocker when v2 face/body/coverage fields are complete. This avoids false rejection of otherwise valid full-body inputs.

## Expected vs Actual

| Asset | Expected | Actual policy decision | Main rejection reasons |
| --- | --- | --- | --- |
| `good_front.jpg` | allowed | allowed | none |
| `side_pose.jpg` | allowed / allowed_with_warning | allowed | none |
| `blurry_dark.jpg` | blocked | blocked | `face_not_fully_visible`, `confidence_below_minimum`, `uncertainty_too_high` |
| `multiple_people.jpg` | blocked | blocked | `multiple_subjects_detected`, `insufficient_body_coverage` |
| `multiple_people_masks.jpg` | blocked | blocked | `multiple_subjects_detected`, `face_not_fully_visible`, `human_occlusion_risk_too_high` |
| `not_human.jpg` | blocked | blocked | `no_human_subject_detected`, `face_not_visible`, `body_regions_not_visible` |
| `cropped_face_only.jpg` | blocked / request_better_input | blocked | `tight_headshot_crop`, `insufficient_body_coverage`, `required_regions_missing` |
| `face_hidden.jpg` | blocked / request_better_input | blocked | `face_not_fully_visible`, `human_occlusion_risk_too_high`, `required_regions_missing` |

## Counts

- Critical false pass count: 0
- False reject count in backend policy: 0
- Live provider false reject previously observed for `good_front.jpg`: fixed by removing `preservation_targets_missing` as a hard blocker.

## Verification

Local verification:

- `tests/test_try_on_human_identity_policy.py tests/test_try_on_human_identity_analysis_adapter.py tests/test_try_on_human_identity_workflow.py`: 37 passed
- `tests -k "human_identity"`: 38 passed, 627 deselected, 1 warning
- `scripts/check_architecture.py`: passed

Staging verification:

- API and worker images rebuilt via `scripts/deploy_portable_runtime.sh`.
- Platform foundation smoke returned `readiness_status=ready`.
- API and worker containers are healthy.
- Rebuilt container no longer contains `preservation_targets_missing` as a blocker.
- Staging policy matrix output saved to `output/human_identity_policy_matrix_after_image_rebuild_20260616.json`.

## Remaining Risk

The live Gemini provider acceptance rerun could not be completed end-to-end for all 8 assets during this pass because the provider returned `429 RESOURCE_EXHAUSTED`. This is a provider quota/runtime availability issue, not a backend policy failure.

Next clean validation window should run the same 8-asset live acceptance again after quota recovers.
