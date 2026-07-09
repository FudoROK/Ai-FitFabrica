# Portable Staging Runtime

This runbook starts Ai Fitfabrica on a vendor-neutral contour:

- `api`
- `worker`
- `postgres`
- `redis`
- `minio`
- `qdrant`

Google Cloud, Yandex Cloud, and a plain VPS are treated only as infrastructure hosts. Runtime state and storage stay portable.

## Files

- `.env.portable-staging.example`
- `.env.portable-staging.local`
- `docker-compose.portable-staging.yml`

## Quick Start

1. Create `.env.portable-staging.local` from `.env.portable-staging.example`.
2. Fill secrets and staging-specific values.
3. Verify that Docker, hardware virtualization, and the compose file are ready:

```powershell
python scripts/portable_infrastructure_preflight.py --require-ready
```

If the result reports `hardware_virtualization_unavailable`, enable CPU virtualization
in BIOS/UEFI and the Windows virtualization/WSL components before continuing.

4. Start the contour:

```powershell
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-staging.local up --build -d
```

5. Apply migrations:

```powershell
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-staging.local exec api alembic upgrade head
```

6. Check health:

```powershell
curl.exe http://127.0.0.1:8080/health -H "X-Status-Token: <STATUS_ENDPOINT_TOKEN>"
```

7. Check portable deployment readiness from the env file:

```powershell
python scripts/platform_foundation_smoke.py --env-file .env.portable-staging.local --require-ready
```

## Runtime Mapping

- PostgreSQL: `postgres:5432`
- Redis: `redis:6379`
- MinIO S3 endpoint: `http://minio:9000`
- Qdrant: `http://qdrant:6333`
- API: `http://127.0.0.1:8080`
- MinIO console: `http://127.0.0.1:9001`

## Why This Contour

- avoids lock-in to one cloud vendor data plane;
- keeps Fitfabrica storage and runtime portable;
- preserves the existing backend contracts and adapters;
- allows later relocation to another cloud or a VPS with minimal env changes.
