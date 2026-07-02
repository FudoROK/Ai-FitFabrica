#!/usr/bin/env bash
set -euo pipefail

cd /opt/fitfabrica

token="$(
  sudo docker inspect fitfabrica-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | sed -n 's/^ADMIN_API_TOKEN=//p' \
    | tail -n 1
)"

if [ -z "${token}" ]; then
  echo "acceptance_status=blocked reason=admin_token_not_found"
  exit 1
fi

export FITFABRICA_ADMIN_API_TOKEN="${token}"
python3 /tmp/fitfabrica_catalog_acceptance/load_realistic_business_catalog_staging.py \
  --base-url https://api.fit.aisoulfabrica.com \
  --pack-dir /tmp/fitfabrica_catalog_acceptance/import_ready \
  --poll-index-seconds 180 \
  --allow-category-blocks
