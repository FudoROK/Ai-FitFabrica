# Human Identity Agent Acceptance Report

Date: 2026-06-16
Environment: staging API `https://api.fit.aisoulfabrica.com`
Input folder: `C:\Code\Ai Fitfabrica\test-assets\human-identity`
Garment reference: `apps/web/public/images/for-you/images/for-you-reference-kiri-coat.webp`

## Result Summary

8 images were tested through the real backend workflow. The Human Identity Agent was invoked through the production `AgentInvocationService` path and persisted `try_on_human_identity_analyses` rows.

| File | Job status | Human verdict | Confidence | Uncertainty | Face visibility | Assessment |
| --- | --- | --- | ---: | --- | --- | --- |
| `good_front.jpg` | completed | allowed | 0.95 | low | fully_visible | Pass |
| `side_pose.jpg` | completed | allowed | 0.98 | low | fully_visible | Pass |
| `blurry_dark.jpg` | failed | blocked | 0.55 | high | partially_visible | Pass: correctly blocked |
| `multiple_people.jpg` | failed | blocked | 0.75 | medium | partially_visible | Pass with weak reason: blocked by confidence only |
| `multiple_people_masks.jpg` | failed | blocked | 0.30 | high | occluded | Pass |
| `not_human.jpg` | failed | blocked | 1.00 | low | not_visible | Pass |
| `cropped_face_only.jpg` | completed | allowed | 0.85 | low | fully_visible | Risk: should not proceed to Try-On because lower body and arms are missing |
| `face_hidden.jpg` | failed | allowed | 0.80 | low | partially_visible | Risk: Human stage allowed masked/hat-obscured face; job later failed at instruction stage |

## Key Findings

- The agent runtime works: all tested files created backend jobs, invoked the Human Identity Agent, and persisted structured snapshots.
- Correctly blocked: blurry/dark image, multiple people with masks, non-human image.
- Partially acceptable: multiple people image was blocked, but only by confidence threshold. Backend should have an explicit multiple-subject / ambiguous-subject rejection reason.
- Not acceptable for production confidence: `cropped_face_only.jpg` was allowed even though Try-On needs enough body-region visibility for garment placement.
- Not acceptable for production confidence: `face_hidden.jpg` was allowed by Human Identity despite significant face occlusion; the workflow failed later at Try-On Instruction, which is too late.

## Recommended Remediation

Status: implemented locally after this report and pending post-deploy acceptance verification.

1. Add backend-owned Human Identity suitability policy rules:
   - require `face_visibility == fully_visible` for normal Try-On;
   - block or request better input when face is `partially_visible` with limitations indicating mask/hat/heavy occlusion;
   - require visible body regions needed for Try-On, at minimum face, torso, arms or legs depending on workflow mode;
   - block tight headshot crops for full-body Try-On;
   - block multi-person ambiguity explicitly, not only via confidence.
2. Extend `HumanIdentityContract` or backend mapper with explicit fields if needed:
   - `subject_count`;
   - `crop_quality`;
   - `try_on_body_coverage`;
   - `occlusion_risk`.
3. Add acceptance tests using these exact assets as fixtures or a small non-sensitive golden fixture set.
4. Re-run this acceptance matrix after policy hardening and require:
   - `good_front.jpg` allowed;
   - `side_pose.jpg` allowed or allowed-with-warning;
   - all poor/ambiguous/non-human/cropped/occluded inputs blocked before instruction/generation.

## Evidence Artifacts

- Job run JSON: `output/human_identity_acceptance_jobs_20260616.json`
- Database export CSV: `output/human_identity_acceptance_db_20260616.csv`
