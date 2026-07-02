# Try-On Real Activation Runbook

This runbook is the operator gate for enabling the real Vertex Virtual Try-On path.
The default public staging backend must stay safe until this runbook is executed deliberately.

## Activation Boundary

Real Try-On generation is active only when all of these settings are true in the target environment:

- `TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on`
- `ENABLE_REAL_TRY_ON_GENERATION=true`
- `VERTEX_PROJECT` points to the intended GCP project
- object storage, PostgreSQL, Redis, and worker queue are configured

If the backend is left in `sandbox_fake`, the public site can be deployed safely but it will not run paid live generation.

## Required Environment

Start from:

- `docs/runbooks/try_on_real_activation_staging.env.example`

The staging environment must include:

- `ENVIRONMENT=staging`
- `TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on`
- `ENABLE_REAL_TRY_ON_GENERATION=true`
- `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none`
- `OBJECT_STORAGE_BACKEND=s3`
- `POSTGRES_DSN=...`
- `OPERATIONS_QUEUE_BACKEND=redis`
- `REDIS_URL=...`

## Fallback Policy

Default production-like policy:

- `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none`

Do not silently downgrade from real Vertex generation to fake or provider-runtime generation in staging/prod.
If controlled non-production fallback is needed, it must be explicitly enabled and documented before rollout.

## Dry Run

Run from the VM or the same environment that will host the API and worker:

```bash
cd /opt/fitfabrica
python scripts/try_on_real_activation_smoke.py --env-file .env.portable-remote-staging.local
```

For a hard deployment gate, require ready state:

```bash
cd /opt/fitfabrica
python scripts/try_on_real_activation_smoke.py --env-file .env.portable-remote-staging.local --require-ready
```

Expected ready state:

- `/health` reports `backend=vertex_virtual_try_on`
- `/health` reports `activation_enabled=true`
- `/health` reports `readiness_status=ready`
- `scripts/try_on_real_activation_smoke.py --require-ready` exits successfully

## Staging Rollout Checklist

1. Confirm VM service account has `roles/aiplatform.user`.
2. Confirm VM OAuth scope includes `https://www.googleapis.com/auth/cloud-platform`.
3. Confirm object storage writes succeed.
4. Confirm API and worker use the same env file.
5. Confirm `TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none`.
6. Run `scripts/platform_foundation_smoke.py --require-ready`.
7. Run `scripts/try_on_real_activation_smoke.py --require-ready`.
8. Run Try-On HTTP/worker live smoke with a small approved asset pair.
9. Restore sandbox mode if the environment is not intended to keep paid generation enabled.

## Rollback

To disable real paid generation:

```env
TRY_ON_GENERATION_BACKEND=sandbox_fake
ENABLE_REAL_TRY_ON_GENERATION=false
TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none
```

Then redeploy/recreate `api` and `worker`, and verify `/health`.

## No Silent Downgrade

The system must fail closed for real activation mistakes.
If real Try-On is requested but readiness is invalid, generation must not silently continue through a fake backend.
