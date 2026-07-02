#!/usr/bin/env bash
set -euo pipefail

token="$(
  sudo docker inspect fitfabrica-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | sed -n 's/^ADMIN_API_TOKEN=//p' \
    | tail -n 1
)"

if [ -z "${token}" ]; then
  echo "post_acceptance_status=blocked reason=admin_token_not_found"
  exit 1
fi

pending="$(
  curl -sS -f \
    "https://api.fit.aisoulfabrica.com/api/admin/business-catalog/products/pending" \
    -H "Authorization: Bearer ${token}"
)"
echo "pending_response=${pending}"

search="$(
  curl -sS -f \
    -X POST "https://api.fit.aisoulfabrica.com/api/similar-search" \
    -H "Content-Type: application/json" \
    -d '{"source_type":"text","query_text":"Белая оверсайз рубашка","category":"shirt","limit":10,"user_country_code":"KZ","user_city":"Almaty"}'
)"
echo "structured_search_response=${search}"
