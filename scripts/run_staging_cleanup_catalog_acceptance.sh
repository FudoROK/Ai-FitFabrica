#!/usr/bin/env bash
set -euo pipefail

token="$(
  sudo docker inspect fitfabrica-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | sed -n 's/^ADMIN_API_TOKEN=//p' \
    | tail -n 1
)"

if [ -z "${token}" ]; then
  echo "cleanup_status=blocked reason=admin_token_not_found"
  exit 1
fi

export FITFABRICA_ADMIN_API_TOKEN="${token}"
python3 /tmp/fitfabrica_catalog_acceptance/cleanup_staging_catalog_acceptance_products.py \
  --created-at-prefix 2026-07-02T08:15
