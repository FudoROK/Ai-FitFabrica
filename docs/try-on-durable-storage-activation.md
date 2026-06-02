# Try-On Durable Storage Activation

## Activation Boundary

Durable storage activation only changes where Try-On uploads and job aggregates are persisted. It does not enable Vertex, Gemini, Imagen, real AI generation, credits deduction, marketplace search, repair, or retry workflows.

## Required Environment

- `OBJECT_STORAGE_BACKEND=s3`
- `OBJECT_STORAGE_BUCKET_NAME=<approved bucket name>`
- `OBJECT_STORAGE_ENDPOINT_URL=<provider endpoint if required>`
- `POSTGRES_DSN=<approved postgres dsn>`

Defaults remain `in_memory`. Do not set the S3/PostgreSQL values in local development unless the operator is deliberately testing durable storage.

## IAM

The Cloud Run service account must have only the minimum permissions needed for the approved resources:

- write objects to the configured object storage bucket/prefix;
- access the approved PostgreSQL runtime through the deployed application network boundary.

Do not grant broad owner/editor roles for this activation.

## Dry Run

Run:

```powershell
python scripts/try_on_storage_smoke.py
```

Expected output includes:

```text
dry_run=true
live_write_check=false
No S3 or PostgreSQL write was attempted.
```

## Live Write Boundary

This activation gate intentionally does not perform live write probes automatically. A real write probe requires a separate approved plan or a direct explicit operator command after bucket, PostgreSQL, IAM, and rollback have been confirmed.

## Rollback

To roll back durable storage routing, set:

```text
OBJECT_STORAGE_BACKEND=in_memory
```

Redeploy the backend with those settings. Existing PostgreSQL/object-storage data is not deleted by rollback.

## No Vertex

Durable storage activation does not call Vertex or production image generation. Try-On generation remains the sandbox fake adapter until a separate generation plan is approved.
