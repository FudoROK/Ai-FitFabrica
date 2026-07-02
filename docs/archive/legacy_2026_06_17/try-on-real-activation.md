# Try-On Real Vertex Activation

## Activation Boundary

This activation enables the real backend-owned Vertex Virtual Try-On generation path. It does not move agent orchestration into the frontend, bypass backend quality verification, disable repair, or allow direct browser access to Vertex.

## Required Environment

- `TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on`
- `ENABLE_REAL_TRY_ON_GENERATION=true`
- `VERTEX_PROJECT=<approved vertex project>`
- `VERTEX_VIRTUAL_TRY_ON_LOCATION=<approved location>`
- `VERTEX_VIRTUAL_TRY_ON_MODEL=<approved model>`
- `OBJECT_STORAGE_BACKEND=s3`
- `OBJECT_STORAGE_BUCKET_NAME=<approved bucket name>`
- `POSTGRES_DSN=<approved postgres dsn>`
- `OPERATIONS_QUEUE_BACKEND=redis`
- `REDIS_URL=<approved redis url>`

If any of these requirements are missing, startup must fail fast. The backend must not silently downgrade a requested real Vertex path.

## Fallback Policy

- Default: `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none`
- Allowed non-production rollout values: `provider_runtime` or `sandbox_fake`
- Production-like environments must keep `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none`

If a production-like rollout intentionally needs fallback behavior, that unsafe posture must be made explicit with:

```text
ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION=true
```

## Dry Run

Validate config without running a live Try-On job:

```powershell
python scripts/try_on_real_activation_smoke.py
```

Expected output includes:

```text
try_on_real_activation_smoke
readiness_status=inactive
```

For deployed environments, the same dry-run view is exposed through `/health` under the `try_on_real_activation` block.
Use `docs/try-on-real-activation-staging.env.example` as the starting pack for staging values.
Use `docs/try-on-real-activation-staging-fill-template.md` as the operator fill-in worksheet before producing the final env file.

To validate a specific staging pack file before export or deployment:

```powershell
python scripts/try_on_real_activation_smoke.py --env-file docs/try-on-real-activation-staging.env.example
```

For staging rollout gates, require an explicit ready verdict:

```powershell
python scripts/try_on_real_activation_smoke.py --env-file <filled-staging-env-file> --require-ready
```

Use `--require-ready` in operator runbooks or deployment checks only when the target environment is intentionally prepared to activate the real path.

## Staging Rollout Checklist

1. Confirm `TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on` and `ENABLE_REAL_TRY_ON_GENERATION=true` only in the target staging environment.
2. Confirm `OBJECT_STORAGE_BACKEND=s3`, `POSTGRES_DSN`, `OPERATIONS_QUEUE_BACKEND=redis`, and `REDIS_URL` point to approved staging resources.
3. Confirm `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none` unless the rollout explicitly allows controlled non-production downgrade behavior.
4. Start from `docs/try-on-real-activation-staging.env.example` and replace every placeholder with approved staging values.
5. Run `python scripts/try_on_real_activation_smoke.py --require-ready` and require `readiness_status=ready`.
6. Check deployed `/health` and confirm the `try_on_real_activation.readiness_status` field is `ready`.
7. Enable the path only for controlled internal staging traffic before any broader rollout.

## Go / No-Go

- Go: `readiness_status=ready`, fallback policy matches rollout intent, and the environment is limited to controlled staging traffic.
- No-Go: any `blocked` check, any unexpected fallback, or any staging resource mismatch.

## Rollback

To disable the real Vertex path, set:

```text
ENABLE_REAL_TRY_ON_GENERATION=false
TRY_ON_GENERATION_BACKEND=sandbox_fake
TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none
```

Then redeploy the backend. Existing persisted job records and artifacts are not deleted by rollback.

## No Silent Downgrade

The backend must fail on unsafe real-path startup config instead of quietly switching to another generation backend. Fallback is allowed only when the operator configured it explicitly.
