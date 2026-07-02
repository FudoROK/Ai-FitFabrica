# Try-On Durable Storage Activation

This runbook defines the minimum operator gate for enabling durable Try-On storage.

## Activation Boundary

Durable storage is active only when uploads, intermediate files, final images, quality reports, and repair artifacts are written through backend-owned object storage and metadata is persisted in SQL.

## Required Environment

Required settings:

- `OBJECT_STORAGE_BACKEND=s3`
- `OBJECT_STORAGE_BUCKET_NAME=<bucket>`
- `OBJECT_STORAGE_ENDPOINT_URL=<endpoint>`
- `OBJECT_STORAGE_ACCESS_KEY_ID=<access-key>`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY=<secret>`
- `POSTGRES_DSN=<sql-dsn>`

## IAM

For GCP-hosted VMs, the VM service account needs only the permissions required for the selected provider calls.
S3-compatible object storage credentials must remain in VM-local env or Secret Manager and must not be committed.

## Dry Run

Run from the target environment:

```bash
cd /opt/fitfabrica
python scripts/try_on_storage_smoke.py
```

Expected:

- upload write succeeds
- artifact read succeeds
- SQL-backed job status can reference the stored artifact

## Rollback

Disable durable storage only for local development:

```env
OBJECT_STORAGE_BACKEND=memory
```

Do not use memory storage for staging/prod acceptance.

## No Vertex

This activation is storage-only. It does not enable real Vertex Try-On generation by itself.
