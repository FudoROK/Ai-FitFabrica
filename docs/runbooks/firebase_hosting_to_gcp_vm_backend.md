# Firebase Hosting To GCP VM Backend

This runbook connects the existing Firebase-hosted frontend to a portable backend running on a plain GCP VM.

Target shape:

- `Firebase Hosting` serves the public site and workspace frontend
- `GCP VM` runs the portable backend contour
- browser calls go from Firebase frontend to the backend API base URL

The cloud vendor remains only the host.  
Backend runtime and stateful services stay under our control.

## What Lives Where

Firebase Hosting:

- static frontend build from `apps/web`
- browser-side `NEXT_PUBLIC_API_BASE_URL`

GCP VM:

- `api`
- `worker`
- `postgres`
- `redis`
- `minio`
- `qdrant`
- reverse proxy in front of `api`

## Required DNS

Current live hostnames:

- frontend: `https://fit.aisoulfabrica.com`
- backend: `https://api.fit.aisoulfabrica.com`

Recommended general pattern for future environments:

- frontend: `<env>.fitfabrica.ai` or your current public site host
- backend: `api.<frontend-host>` or `api-<env>.fitfabrica.ai`

## GCP VM Baseline

Use the portable VM baseline from:

- `docs/runbooks/portable_remote_staging_ubuntu_22_04.md`

Recommended first host:

- Ubuntu `22.04 LTS`
- `e2-standard-4` or similar
- `80 GB` SSD
- one public IP

Allow inbound:

- `22/tcp` from operator IPs only
- `80/tcp` from the internet
- `443/tcp` from the internet

Do not expose:

- `5432`
- `6379`
- `9000`
- `9001`
- `6333`
- `8080`

## Backend Env Contract

Start from:

- `.env.portable-remote-staging.example`

Set at least:

- `MESSAGING_PROVIDER=none`
- `CADDY_SITE_ADDRESS=api.fit.aisoulfabrica.com`
- `APP_HOST=0.0.0.0`
- `APP_PORT=8080`
- `PUBLIC_STATUS_ENDPOINTS_ENABLED=true`
- `STATUS_ENDPOINT_TOKEN=<real-token>`
- `POSTGRES_DSN=postgresql+asyncpg://fitfabrica:<password>@postgres:5432/fitfabrica`
- `REDIS_URL=redis://redis:6379/0`
- `OBJECT_STORAGE_BACKEND=s3`
- `OBJECT_STORAGE_BUCKET_NAME=fitfabrica-staging`
- `OBJECT_STORAGE_ENDPOINT_URL=http://minio:9000`
- `OBJECT_STORAGE_ACCESS_KEY_ID=<minio-access-key>`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY=<minio-secret>`
- `QDRANT_URL=http://qdrant:6333`
- `OPERATIONS_QUEUE_BACKEND=redis`
- `OPERATIONS_WORKER_NAME=portable-worker`

For the standard Firebase-to-backend path, use the web-first backend only.  
Telegram and Pub/Sub ingress are removed from the active deployment baseline.

For Firebase frontend access, set browser origins explicitly:

- `CORS_ALLOWED_ORIGINS=https://<firebase-frontend-host>`
- or `CORS_ALLOWED_ORIGIN_REGEX=^https://[a-z0-9-]+\.(web\.app|firebaseapp\.com)$` for Firebase default domains

Example:

```env
CORS_ALLOWED_ORIGINS=https://fit.aisoulfabrica.com
```

If you serve the frontend on both Firebase default domain and custom domain, include both:

```env
CORS_ALLOWED_ORIGINS=https://fit.aisoulfabrica.com,https://ai-fitfabrica.web.app
```

If the frontend still uses the default Firebase domains and the final custom domain is not ready yet, use:

```env
CORS_ALLOWED_ORIGIN_REGEX=^https://[a-z0-9-]+\.(web\.app|firebaseapp\.com)$
```

## Backend Bring-Up

On the VM:

```bash
cd /opt/fitfabrica
cp .env.portable-remote-staging.example .env.portable-remote-staging.local
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local build api
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local run --rm --no-deps api python scripts/platform_foundation_smoke.py --require-ready
bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local
```

Run migrations:

```bash
docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local exec -T api alembic upgrade head
```

## Reverse Proxy And TLS

Start from:

- `deploy/caddy/Caddyfile.portable.example`
- `deploy/caddy/Caddyfile.portable-vm-http`

Point it at:

- `127.0.0.1:8080`

Recommended public backend URL:

```text
https://api.fit.aisoulfabrica.com
```

The compose proxy service can obtain certificates automatically once:

- DNS already points to the VM IP
- `CADDY_SITE_ADDRESS` matches that public hostname
- inbound `80/tcp` and `443/tcp` are open

## Backend Verification

From the VM:

```bash
curl -H "X-Status-Token: <STATUS_ENDPOINT_TOKEN>" http://127.0.0.1:8080/health
```

From outside the VM after proxy/TLS:

```bash
curl -H "X-Status-Token: <STATUS_ENDPOINT_TOKEN>" https://api.fit.aisoulfabrica.com/health
```

Expected:

```text
operations_queue_backend=redis
```

And a healthy JSON response.

## Firebase Frontend Env

The frontend reads:

- `NEXT_PUBLIC_API_BASE_URL`

Start from:

- `apps/web/.env.firebase.example`

Set:

```env
NEXT_PUBLIC_API_BASE_URL=https://api.fit.aisoulfabrica.com
```

Temporary bring-up fallback before DNS/TLS:

```env
NEXT_PUBLIC_API_BASE_URL=http://34.140.131.192
```

For local verification:

```bash
cd apps/web
cp .env.firebase.example .env.local
```

Then build:

```bash
npm install
npm run lint
npm run typecheck
npm run build
```

## Firebase Hosting Deploy

The repo already contains:

- `firebase.json`

Deploy the frontend after the backend URL is real and healthy:

```bash
firebase deploy --only hosting
```

The current hosting config uses:

- static export from `apps/web/out`
- `cleanUrls: true`
- no catch-all rewrite to `/index.html`

For Firebase static hosting compatibility, workspace navigation uses plain anchor links instead of relying on Next app-router prefetch/RSC fetch behavior.

## Browser-Side Integration Contract

The current frontend expects the backend base URL to expose:

- `POST /demo-request`
- `POST /auth/sign-in`
- `POST /api/try-on/jobs`
- `GET /api/jobs/{job_id}/status`
- `GET /api/jobs/{job_id}/result`

Do not point `NEXT_PUBLIC_API_BASE_URL` at Firebase Hosting itself.  
It must point at the backend API hostname.

## End-To-End Smoke

1. Open the Firebase-hosted frontend.
2. Verify no immediate browser CORS errors.
3. Open `/workspace/new-fitting`.
4. Upload two images.
5. Confirm the browser calls `POST /api/try-on/jobs` on the backend hostname.
6. Confirm the backend returns a job id.
7. Confirm polling/status and result routes work.
8. Confirm worker logs show the workflow execution.

## Done Means

This integration step is complete only when:

- Firebase frontend uses a real `NEXT_PUBLIC_API_BASE_URL`
- backend CORS allows the Firebase origin
- GCP VM backend passes portable readiness and health checks
- browser can create a Try-On job without local dev fallbacks
- live custom domains answer on both frontend and backend hosts
