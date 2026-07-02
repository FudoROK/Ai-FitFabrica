# Portable Remote Staging VM

This runbook deploys Ai Fitfabrica to a plain Linux VM or VPS with a portable data plane:

- `api`
- `worker`
- `postgres`
- `redis`
- `minio`
- `qdrant`

The cloud vendor is only the host. Runtime data services stay under our control.

## Required VM Baseline

- Ubuntu 22.04 or Debian 12
- 4 vCPU
- 8 GB RAM
- 80+ GB SSD
- public IP
- Docker Engine + Docker Compose plugin

## Required Open Ports

- `80` / `443` for reverse proxy or direct HTTP ingress
- `8080` only if you intentionally expose the app directly

Do not expose `5432`, `6379`, `9000`, `9001`, or `6333` publicly unless you have a deliberate network policy for them.

## Files

- `docker-compose.portable-staging.yml`
- `.env.portable-remote-staging.example`
- `.env.portable-remote-staging.local`
- `scripts/bootstrap_portable_host.sh`
- `scripts/deploy_portable_runtime.sh`
- `deploy/caddy/Caddyfile.portable.example`
- `docs/runbooks/portable_remote_staging_ubuntu_22_04.md`

## Preparation

1. Copy `.env.portable-remote-staging.example` to `.env.portable-remote-staging.local`.
2. Replace all placeholder values.
3. Copy the repository or deployment bundle to the VM.
4. Bootstrap Docker on a fresh Ubuntu/Debian host:

```bash
sudo bash scripts/bootstrap_portable_host.sh
```

## Start

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local up --build -d
```

Or use the deployment wrapper:

```bash
bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local
```

## Migrations

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local exec api alembic upgrade head
```

## Health Check

```bash
curl -H "X-Status-Token: <STATUS_ENDPOINT_TOKEN>" http://127.0.0.1:8080/health
```

## Portable Runtime Readiness Gate

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local build api
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local run --rm --no-deps api python scripts/platform_foundation_smoke.py --require-ready
```

## B2B Catalog Search Index Readiness Gate

Run this after `alembic upgrade head` and after the API container is up. It verifies that the deployed database has the B2B search-index columns, the indexing runtime is wired, and the worker has the `business_catalog_search_index` handler.

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local exec -T api \
  python scripts/business_catalog_search_index_readiness.py --require-db
```

## Try-On Activation Dry Run

```bash
python scripts/try_on_real_activation_smoke.py --env-file .env.portable-remote-staging.local
```

## Recommended Next Layer

- use `deploy/caddy/Caddyfile.portable.example` as the first reverse-proxy baseline
- terminate TLS at the proxy
- restrict direct access to stateful services
- enable backups for PostgreSQL and MinIO volumes

## Why This Path

- portable across Google Cloud, Yandex Cloud, and plain VPS hosts
- no dependency on managed Google data services
- no dependency on Google-specific storage auth for the core runtime

## Exact Ubuntu Path

For the most concrete first deployment path, use:

- `docs/runbooks/portable_remote_staging_ubuntu_22_04.md`
