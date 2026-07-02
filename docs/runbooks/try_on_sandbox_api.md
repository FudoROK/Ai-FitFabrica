# Try-On Sandbox API Contract

This document defines the public Try-On API contract used by the web workspace and staging smoke tests.

## Endpoints

- `POST /api/try-on/jobs` creates a Try-On job from human and garment uploads.
- `GET /api/jobs/{job_id}/status` returns backend-owned lifecycle status.
- `GET /api/jobs/{job_id}/result` returns the final result after the worker completes the job.

Frontend clients must not call model providers directly and must not calculate credits or workflow decisions.

## Lifecycle

The backend owns all lifecycle decisions. Expected public statuses include:

- `accepted`
- `analyzing_human`
- `generating`
- `quality_checking`
- `completed`
- `not_ready`
- `job_failed`

`sandbox_lifecycle_mode` is allowed only for non-production safe flows where no paid model call is intended.

## Storage Backend

Durable staging and production-like environments must use backend-owned storage:

- `object_storage_backend=s3`
- object metadata persisted through portable SQL infrastructure
- generated artifacts returned through backend result records

Local in-memory storage is only for tests and isolated development.

## Generation Backends

Supported backend selector:

- `try_on_generation_backend=sandbox_fake|provider_runtime|vertex_virtual_try_on`

`sandbox_fake` is safe for public staging demos where real generation is intentionally disabled.
`provider_runtime` and `vertex_virtual_try_on` must stay behind backend runtime adapters.

## Quality And Repair

Quality verification selector:

- `try_on_quality_verifier_backend=deterministic|model_backed`

Repair selector:

- `try_on_repair_backend=deterministic|provider_runtime`

Repair must never run for identity/body/pose failures. Those cases must be rejected or retried by backend policy.
