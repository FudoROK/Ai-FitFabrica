# Try-On Real Vertex Activation: Staging Fill Template

Заполни этот документ и затем перенеси значения в `docs/try-on-real-activation-staging.env.example` или в отдельный staging env file.

## 1. Environment Identity

- Environment name:
- Owner / operator:
- Date:
- Change ticket / task link:

## 2. Activation Decision

- Enable real Try-On now? (`yes/no`):
- Target backend: `vertex_virtual_try_on`
- `ENABLE_REAL_TRY_ON_GENERATION`: `true`
- Fallback policy:
  `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=`
- If fallback is not `none`, explain why:

## 3. Vertex

- `VERTEX_PROJECT=`
- `VERTEX_VIRTUAL_TRY_ON_LOCATION=`
- `VERTEX_VIRTUAL_TRY_ON_MODEL=`

## 4. Durable Runtime

- `OBJECT_STORAGE_BACKEND=s3`
- `OBJECT_STORAGE_BUCKET_NAME=`
- `OBJECT_STORAGE_REGION=`
- `OBJECT_STORAGE_ENDPOINT_URL=`
- `OBJECT_STORAGE_ACCESS_KEY_ID=`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY=`
- `POSTGRES_DSN=`
- `OPERATIONS_QUEUE_BACKEND=redis`
- `REDIS_URL=`
- `OPERATIONS_WORKER_NAME=`

## 5. Status / Readiness Access

- `PUBLIC_STATUS_ENDPOINTS_ENABLED=`
- `STATUS_ENDPOINT_TOKEN=`

## 6. Expected Readiness Gate

- Command to run:

```powershell
python scripts/try_on_real_activation_smoke.py --env-file <filled-staging-env-file> --require-ready
```

- Expected result:
  `readiness_status=ready`

## 7. Staging Traffic Boundary

- Who can use this path in staging?
- How is traffic limited?
- Rollback owner:

## 8. Go / No-Go Notes

- Go conditions:
- No-Go conditions:
- Final approval:
