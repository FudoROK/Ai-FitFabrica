#!/usr/bin/env bash
set -euo pipefail

token="$(
  sudo docker inspect fitfabrica-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | sed -n 's/^ADMIN_API_TOKEN=//p' \
    | tail -n 1
)"

if [ -z "${token}" ]; then
  echo "approve_status=blocked reason=admin_token_not_found"
  exit 1
fi

for attempt in 1 2 3; do
  response="$(
    curl -sS -f \
      -X POST "https://api.fit.aisoulfabrica.com/api/admin/business-catalog/products/approve-matched-batch" \
      -H "Authorization: Bearer ${token}" \
      -H "Content-Type: application/json" \
      -d '{"limit":25}'
  )"
  echo "approve_batch_response[${attempt}]=${response}"
  if echo "${response}" | grep -q '"processed_count":0'; then
    break
  fi
done
