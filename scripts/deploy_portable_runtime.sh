#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

ENV_FILE="${1:-.env.portable-remote-staging.local}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.portable-staging.yml}"
STATUS_URL="${STATUS_URL:-http://127.0.0.1:8080/health}"

cd "${PROJECT_ROOT}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Env file not found: ${ENV_FILE}" >&2
  exit 1
fi

python scripts/platform_foundation_smoke.py --env-file "${ENV_FILE}" --require-ready
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up --build -d
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T api alembic upgrade head

STATUS_ENDPOINT_TOKEN="$(grep -E '^STATUS_ENDPOINT_TOKEN=' "${ENV_FILE}" | tail -n 1 | cut -d '=' -f 2- || true)"
if [[ -n "${STATUS_ENDPOINT_TOKEN}" ]]; then
  curl --fail --silent --show-error -H "X-Status-Token: ${STATUS_ENDPOINT_TOKEN}" "${STATUS_URL}" >/dev/null
fi

echo "Portable runtime deployed successfully."
