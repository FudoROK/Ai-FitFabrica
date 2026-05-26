# Try-On Durable Storage Activation

## Activation Boundary

Durable storage activation only changes where Try-On uploads and job aggregates are persisted. It does not enable Vertex, Gemini, Imagen, real AI generation, credits deduction, marketplace search, repair, or retry workflows.

## Required Environment

- `TRY_ON_FILE_STORAGE_BACKEND=gcs`
- `TRY_ON_JOB_REPOSITORY_BACKEND=firestore`
- `TRY_ON_GCS_BUCKET_NAME=<approved bucket name>`
- `TRY_ON_GCS_UPLOAD_PREFIX=try-on/uploads`
- `TRY_ON_FIRESTORE_COLLECTION=try_on_jobs`

Defaults remain `in_memory`. Do not set the GCS/Firestore values in local development unless the operator is deliberately testing durable storage.

## IAM

The Cloud Run service account must have only the minimum permissions needed for the approved resources:

- write objects to the configured GCS bucket prefix;
- read/write documents in the configured Firestore collection.

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
No GCS or Firestore write was attempted.
```

## Live Write Boundary

This activation gate intentionally does not perform live write probes automatically. A real write probe requires a separate approved plan or a direct explicit operator command after bucket, Firestore, IAM, and rollback have been confirmed.

## Rollback

To roll back durable storage routing, set:

```text
TRY_ON_FILE_STORAGE_BACKEND=in_memory
TRY_ON_JOB_REPOSITORY_BACKEND=in_memory
```

Redeploy the backend with those settings. Existing Firestore/GCS data is not deleted by rollback.

## No Vertex

Durable storage activation does not call Vertex or production image generation. Try-On generation remains the sandbox fake adapter until a separate generation plan is approved.
