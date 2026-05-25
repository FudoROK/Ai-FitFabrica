# Try-On Sandbox Lifecycle Design

## Purpose

Build the first end-to-end Try-On workflow for AI FitFabrica using the existing `apps/web` product surface and real backend-owned API endpoints. This cycle proves the job lifecycle, multipart upload contract, status polling, result shape, history/result persistence contract, and sandbox credit events before introducing GCS, Firestore, Vertex, or real AI generation.

## Approved Scope

The first cycle includes:

- Real backend endpoints consumed by `apps/web` through a typed API client and configurable backend base URL.
- `POST /api/try-on/jobs` with `multipart/form-data`.
- Required `human_photo` and `garment_photo` uploads.
- Backend file validation for required files, content type, size, and empty files.
- A typed `try_on` job model with explicit status history.
- An in-memory sandbox job repository.
- A deterministic fake Try-On generation adapter behind a generation port.
- A structurally realistic result contract.
- A fake quality report that matches the future Quality Verifier Agent result shape.
- Sandbox credit/cost events marked as `not_charged`.
- Existing `apps/web` Try-On page integration.
- Backend and frontend verification for the first workflow.

This cycle excludes:

- GCS.
- Firestore persistence.
- Vertex or real AI generation.
- Marketplace search.
- Product Card.
- Similar Search.
- Real credit deduction or billing.
- New frontend applications or alternate UI surfaces.

## Backend Contract

Backend owns the Try-On workflow lifecycle. The frontend never creates job IDs, calculates credits, chooses fake versus real generation, or implements workflow state transitions.

### `POST /api/try-on/jobs`

Request:

- Content type: `multipart/form-data`.
- Required field: `human_photo`.
- Required field: `garment_photo`.
- Optional workflow parameters can be accepted only when typed and backend-validated.

Response:

- `job_id`.
- `workflow_type: "try_on"`.
- `status`.
- Accepted input metadata.
- `status_url`.
- `result_url`.

Backend behavior:

- Validate both files.
- Extract sandbox-safe metadata such as original filename, content type, size, and checksum.
- Create a typed `try_on` job.
- Record explicit status transitions.
- Call the fake generation adapter through the generation port.
- Record a sandbox quality report.
- Record sandbox cost events as `not_charged`.
- Store the job in the in-memory repository.

### `GET /api/jobs/{job_id}/status`

Returns the typed current status and status history for the requested job.

Unknown jobs return a structured typed error.

### `GET /api/jobs/{job_id}/result`

Returns the final result when the job is completed.

If the job exists but is not completed, the endpoint returns a structured `not_ready` response. It does not return plain text and does not invent a result.

Unknown or failed jobs return structured typed responses.

## Domain Model

### `TryOnJob`

Fields:

- `job_id`.
- `workflow_type`.
- `status`.
- `created_at`.
- `updated_at`.
- `input_metadata`.
- `status_history`.
- `cost_events`.
- `result`.
- `error`.

### `TryOnInputMetadata`

One metadata object is stored for `human_photo` and one for `garment_photo`.

Fields:

- `role`.
- `filename`.
- `content_type`.
- `size_bytes`.
- `sha256`.

Raw uploaded images are not persisted permanently in this cycle.

### `TryOnStatusEvent`

Fields:

- `status`.
- `stage`.
- `message`.
- `occurred_at`.

Status transitions are explicit and testable even when the fake workflow completes quickly.

Initial statuses:

- `accepted`.
- `validating_inputs`.
- `generating`.
- `quality_checking`.
- `completed`.
- `failed`.

### `TryOnCostEvent`

Fields:

- `event_type`.
- `estimated_units`.
- `charge_status`.
- `charged_credits`.
- `occurred_at`.

For this cycle, `charge_status` is `not_charged` and `charged_credits` is `0`.

### `TryOnResult`

Fields:

- `job_id`.
- `workflow_type`.
- `result_image`.
- `quality_report`.
- `stylist_note`.
- `input_metadata`.
- `completed_at`.

The fake result can use a placeholder image reference, but the response shape must match the future real result contract.

### `TryOnQualityReport`

The first implementation uses deterministic fake values, but the structure must match the future Quality Verifier Agent output.

Fields:

- `verdict`.
- `confidence`.
- `checks`.
- `limitations`.

Each check includes:

- `name`.
- `status`.
- `confidence`.
- `message`.

## Validation Rules

Backend validation is the source of truth. Frontend validation exists only for immediate user feedback.

Backend must reject:

- Missing `human_photo`.
- Missing `garment_photo`.
- Unsupported content type.
- Empty files.
- Files larger than the configured maximum size.

Allowed content types and maximum size must be configuration-driven. They must not be hidden as magic values inside route handlers.

Structured error responses include:

- `error.code`.
- `error.message`.
- `error.details`.

## Ports And Adapters

### `TryOnJobRepositoryPort`

Stores and reads Try-On jobs.

First adapter: in-memory sandbox repository.

The in-memory repository is acceptable only for the first sandbox lifecycle proof. Jobs are not durable and may disappear after backend restart.

### `TryOnGenerationPort`

Generates a Try-On result from validated input metadata.

First adapter: deterministic fake generator.

The fake generator must not be hardwired into route handlers or frontend code. It should be replaceable by a future real AI adapter without changing the frontend contract.

### `TryOnWorkflowService`

Owns orchestration:

- Validate upload inputs.
- Create the job.
- Record status history.
- Call generation through `TryOnGenerationPort`.
- Record quality report.
- Record sandbox cost events.
- Persist job state through `TryOnJobRepositoryPort`.

## Frontend Integration

Only the existing `apps/web` project is first-class for this cycle. No new frontend or mockup app is created.

### `/workspace/try-on/new`

The page becomes a client-side workflow screen while preserving the current structure and design direction.

Behavior:

- Select `human_photo`.
- Select `garment_photo`.
- Show local previews.
- Validate type and size locally for UX.
- Submit `multipart/form-data` to `POST /api/try-on/jobs`.
- Poll `GET /api/jobs/{job_id}/status`.
- Navigate to `/workspace/try-on/result?job_id={job_id}` when complete.
- Show loading, validation, disabled, error, and success states.

### `/workspace/try-on/result`

The page reads `job_id` from the query string.

Behavior:

- Call `GET /api/jobs/{job_id}/result`.
- Render completed result contract.
- Render a not-ready state if backend returns `not_ready`.
- Render a structured error state for failed or missing jobs.
- Remove hardcoded "perfect result" claims from the working result flow.

### Typed API Client

Add typed methods:

- `createTryOnJob(formData)`.
- `getJobStatus(jobId)`.
- `getJobResult(jobId)`.

The backend base URL remains configurable through environment configuration.

## Testing

Backend tests cover:

- Successful multipart job creation.
- Missing `human_photo`.
- Missing `garment_photo`.
- Unsupported content type.
- Empty file.
- Oversized file.
- Status endpoint for an existing job.
- Result endpoint for completed job.
- Result endpoint structured `not_ready` response.
- Unknown job structured error.
- Status history creation.
- Sandbox `not_charged` cost event creation.
- Fake generator accessed through the generation port boundary.

Frontend verification covers:

- TypeScript typecheck.
- Lint.
- Production build.
- Local manual workflow check if the dev server is available.

## Acceptance Criteria

- `apps/web` calls real backend endpoints for Try-On.
- Backend creates typed `try_on` jobs.
- File validation is performed by backend.
- Errors are structured and typed.
- Status polling returns real backend status.
- Result endpoint returns real backend result contract.
- Fake generation lives behind a backend port/interface.
- In-memory persistence limitation is documented.
- Credits/cost events exist only as sandbox `not_charged` records.
- No GCS, Firestore, Vertex, real AI, Marketplace, Product Card, or Similar Search is introduced in this cycle.
