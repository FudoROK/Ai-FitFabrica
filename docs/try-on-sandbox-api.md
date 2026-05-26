# Try-On Sandbox API Contract

This document records the current AI FitFabrica Try-On sandbox API before durable storage and real generation adapters are introduced.

The sandbox is backend-owned. The web client uploads files, creates a job, polls status/result endpoints, and renders the response. The browser must not call AI providers, calculate credits, or decide workflow repair/retry rules.

## Scope

Included:

- Multipart job creation for one human photo and one garment photo.
- Typed job lifecycle statuses.
- Typed status polling.
- Typed result polling.
- Sandbox-only async lifecycle modes for frontend verification.
- Deterministic fake generation for completed jobs.
- Sandbox cost event with no real credit charge.

Excluded:

- No GCS file storage.
- No Firestore job persistence.
- No Vertex, Gemini, Imagen, or real AI generation.
- No real credits deduction.
- No marketplace search.
- No durable job history after backend restart.

## POST /api/try-on/jobs

Creates a backend-owned Try-On sandbox job.

Request type: `multipart/form-data`.

Required file fields:

- `human_photo`
- `garment_photo`

Accepted content types:

- `image/jpeg`
- `image/png`
- `image/webp`

Default max file size: `10 MB`, configurable through backend settings.

Optional sandbox-only form field:

- `sandbox_lifecycle_mode`

Allowed values:

- `complete` - default. The job completes immediately with a deterministic sandbox result.
- `pending` - the job stops at `generating`; result polling returns `not_ready`.
- `failed` - the job stops at `failed`; result polling returns `job_failed`.

Success response: `201`.

Response body:

```json
{
  "job_id": "try_on_<id>",
  "workflow_type": "try_on",
  "status": "completed",
  "input_metadata": [],
  "status_url": "/api/jobs/try_on_<id>/status",
  "result_url": "/api/jobs/try_on_<id>/result"
}
```

The `status` value can be `completed`, `generating`, or `failed` depending on `sandbox_lifecycle_mode`.

## GET /api/jobs/{job_id}/status

Returns the current job status, full status history, and sandbox cost events.

Success response: `200`.

Response body:

```json
{
  "job_id": "try_on_<id>",
  "workflow_type": "try_on",
  "status": "generating",
  "status_history": [
    {
      "status": "accepted",
      "stage": "accepted",
      "message": "Job accepted.",
      "occurred_at": "2026-05-26T00:00:00Z"
    }
  ],
  "cost_events": [
    {
      "event_type": "try_on_sandbox_generation",
      "estimated_units": 0,
      "charge_status": "not_charged",
      "charged_credits": 0,
      "occurred_at": "2026-05-26T00:00:00Z"
    }
  ]
}
```

Possible statuses:

- `accepted`
- `validating_inputs`
- `generating`
- `quality_checking`
- `completed`
- `failed`

## GET /api/jobs/{job_id}/result

Returns the completed result or a typed lifecycle response.

Completed response: `200`.

```json
{
  "status": "completed",
  "job_id": "try_on_<id>",
  "workflow_type": "try_on",
  "result": {
    "job_id": "try_on_<id>",
    "workflow_type": "try_on",
    "result_image": {
      "kind": "sandbox_placeholder",
      "url": "/images/shared/try-on-sandbox-result.webp",
      "alt": "Sandbox Try-On result preview"
    },
    "quality_report": {
      "verdict": "pass",
      "confidence": 0.91,
      "checks": [],
      "limitations": []
    },
    "stylist_note": "Sandbox Try-On completed.",
    "input_metadata": [],
    "completed_at": "2026-05-26T00:00:00Z"
  }
}
```

Not-ready response: `202`.

```json
{
  "status": "not_ready",
  "job_id": "try_on_<id>",
  "workflow_type": "try_on",
  "current_status": "generating",
  "status_url": "/api/jobs/try_on_<id>/status"
}
```

Failed response: `409`.

```json
{
  "error": {
    "code": "job_failed",
    "message": "Try-On job failed.",
    "details": {
      "job_id": "try_on_<id>"
    }
  }
}
```

## Error Envelope

All typed Try-On API errors use this shape:

```json
{
  "error": {
    "code": "missing_required_file",
    "message": "Human and garment photos are required.",
    "details": {}
  }
}
```

Known error codes:

- `missing_required_file`
- `unsupported_content_type`
- `empty_file`
- `file_too_large`
- `job_not_found`
- `result_not_ready`
- `job_failed`

## Frontend Contract

The web client should:

- Create jobs through `POST /api/try-on/jobs`.
- Poll `GET /api/jobs/{job_id}/result`.
- If result polling returns `not_ready`, call `GET /api/jobs/{job_id}/status`.
- Continue polling until `completed` or `failed`.
- Show backend errors from the typed error envelope.
- Treat credits as display-only sandbox data.

The web client must not:

- Call AI/model providers directly.
- Store secrets.
- Calculate or deduct credits.
- Decide repair/retry workflow rules.
- Persist job state outside backend-owned APIs.
