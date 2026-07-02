# Portable Remote Staging On Ubuntu 22.04

This is the exact first-pass bring-up path for Ai Fitfabrica on a plain Ubuntu 22.04 VM.

The host may live in GCP, Yandex Cloud, Oracle Cloud, Hetzner, or a generic VPS provider.  
The runtime contour stays the same:

- `api`
- `worker`
- `postgres`
- `redis`
- `minio`
- `qdrant`

## Recommended VM Shape

- Ubuntu `22.04 LTS`
- `4 vCPU`
- `8 GB RAM`
- `80 GB SSD`
- `1 public IPv4`

## Required Network Policy

Allow inbound:

- `22/tcp` from your operator IPs only
- `80/tcp` from the internet
- `443/tcp` from the internet

Do not expose:

- `5432/tcp`
- `6379/tcp`
- `9000/tcp`
- `9001/tcp`
- `6333/tcp`
- `8080/tcp` unless you intentionally bypass the reverse proxy

## First Login

Connect to the VM:

```bash
ssh ubuntu@<server-ip>
```

Refresh packages and install the small operator baseline:

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates
```

## Copy The Repository

Use one of these paths:

- `git clone <repo-url> /opt/fitfabrica`
- upload an archive and unpack it to `/opt/fitfabrica`

Recommended ownership:

```bash
sudo mkdir -p /opt/fitfabrica
sudo chown -R "$USER":"$USER" /opt/fitfabrica
```

## Bootstrap Docker

From the repo root:

```bash
cd /opt/fitfabrica
sudo bash scripts/bootstrap_portable_host.sh
```

After the script completes, reconnect your shell so Docker group membership applies:

```bash
exit
ssh ubuntu@<server-ip>
cd /opt/fitfabrica
```

## Prepare The Runtime Env File

Create the staging file:

```bash
cp .env.portable-remote-staging.example .env.portable-remote-staging.local
```

Replace at least these fields before deploy:

- `MESSAGING_PROVIDER=none` for the standard web-first deployment
- `STATUS_ENDPOINT_TOKEN`
- `POSTGRES_DSN`
- `OBJECT_STORAGE_ACCESS_KEY_ID`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY`
- `MEMORY_SUMMARY_TASK_AUTH_AUDIENCE`
- `MEMORY_SUMMARY_TASK_ALLOWED_SERVICE_ACCOUNTS`

For the default single-host portable contour, keep these values unchanged unless you know why you are changing them:

- `POSTGRES_DSN=postgresql+asyncpg://fitfabrica:replace-with-password@postgres:5432/fitfabrica`
- `REDIS_URL=redis://redis:6379/0`
- `OBJECT_STORAGE_ENDPOINT_URL=http://minio:9000`
- `QDRANT_URL=http://qdrant:6333`
- `OPERATIONS_QUEUE_BACKEND=redis`
- `TRY_ON_GENERATION_BACKEND=sandbox_fake`
- `ENABLE_REAL_TRY_ON_GENERATION=false`

Telegram and Pub/Sub ingress are removed from this contour. The deployment baseline is web-first only.

## Validate The Deployment Pack

Before starting containers:

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local build api
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local run --rm --no-deps api python scripts/platform_foundation_smoke.py --require-ready
```

Expected result:

```text
readiness_status=ready
```

## Deploy The Runtime

Use the wrapper:

```bash
bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local
```

Or run the underlying commands manually:

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local up --build -d
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local exec -T api alembic upgrade head
```

## Verify The Containers

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local ps
```

Expected running services:

- `api`
- `worker`
- `postgres`
- `redis`
- `minio`
- `qdrant`

## Verify Health

```bash
curl -H "X-Status-Token: <STATUS_ENDPOINT_TOKEN>" http://127.0.0.1:8080/health
```

## Optional Reverse Proxy

If you want public HTTPS on the same host, start from:

- `deploy/caddy/Caddyfile.portable.example`

Copy it to the host, replace the domain, and point it at `127.0.0.1:8080`.

## Operator Commands

Tail logs:

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local logs -f api worker
```

Restart the runtime:

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local restart
```

Stop the runtime:

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local down
```

## First Production-Like Boundary

This document is still for staging, but it already follows the correct shape:

- single Linux VM
- Docker-owned app runtime
- portable Postgres/Redis/MinIO/Qdrant contour
- no dependency on managed cloud data services
- cloud vendor treated only as infrastructure host
