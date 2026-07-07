# Production Infrastructure Readiness Gate

Use this gate after billing/auth/provider access is restored and before paid live acceptance.

```powershell
.venv\Scripts\python.exe scripts\production_infrastructure_readiness_gate.py --require-production
```

For checking a prepared env file:

```powershell
.venv\Scripts\python.exe scripts\production_infrastructure_readiness_gate.py `
  --env-file ".env.production" `
  --require-production
```

For post-billing staging, check the filled local override:

```powershell
.venv\Scripts\python.exe scripts\production_infrastructure_readiness_gate.py `
  --env-file ".env.post-billing-staging.local" `
  --require-production
```

Expected for production-like environments:

- `POSTGRES_DSN` is configured;
- `REDIS_URL` is configured;
- `OBJECT_STORAGE_BACKEND=s3`;
- `OBJECT_STORAGE_BUCKET_NAME` is configured;
- `OBJECT_STORAGE_ACCESS_KEY_ID` and `OBJECT_STORAGE_SECRET_ACCESS_KEY` are real non-placeholder values;
- `OPERATIONS_QUEUE_BACKEND=redis`;
- `RATE_LIMIT_BACKEND=redis`;
- `RATE_LIMIT_FAIL_MODE=closed`;
- `AUTH_PROVIDER` is not `disabled`;
- `BILLING_CORE_ENABLED=true`;
- `LLM_PROVIDER` is `vertex` or `gemini_structured`, not `fake`;
- `LLM_GATEWAY_MODE` is live/provider mode, not `stub`;
- `IMAGE_EDITING_PROVIDER=google_genai`;
- `TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on`;
- `ENABLE_REAL_TRY_ON_GENERATION=true`;
- `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none`;
- `ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION=false`;
- `ALLOW_UNSAFE_ADMIN_HEADER_AUTH=false`;
- `VERTEX_PROJECT`, `VERTEX_LOCATION`, `VERTEX_VIRTUAL_TRY_ON_LOCATION`, `VERTEX_VIRTUAL_TRY_ON_MODEL`, and `VERTEX_AGENT_RESOURCE` are configured;
- `STATUS_ENDPOINT_TOKEN` and `ADMIN_API_TOKEN` are real non-placeholder values.

If this gate returns `blocked`, do not run paid Try-On, Product Card, Similar Search garment-photo, or provider-backed category validation acceptance.
