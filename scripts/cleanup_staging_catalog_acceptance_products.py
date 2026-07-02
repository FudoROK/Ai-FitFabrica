"""Archive staging business catalog products created by a specific acceptance run."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Archive staging catalog acceptance products.")
    parser.add_argument("--base-url", default="https://api.fit.aisoulfabrica.com")
    parser.add_argument("--created-at-prefix", required=True)
    parser.add_argument("--token-env", default="FITFABRICA_ADMIN_API_TOKEN")
    parser.add_argument("--timeout", type=float, default=60.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        print("cleanup_status=blocked reason=admin_token_missing")
        return 1

    products = _request(args.base_url, "GET", "/api/business/products", args.timeout, token=None)["products"]
    targets = [
        product
        for product in products
        if str(product.get("created_at", "")).startswith(args.created_at_prefix)
    ]
    archived = 0
    failed: list[str] = []
    for product in targets:
        product_id = product["product_id"]
        try:
            _request(
                args.base_url,
                "POST",
                f"/api/admin/business-catalog/products/{product_id}/archive",
                args.timeout,
                token=token,
            )
        except RuntimeError as exc:
            failed.append(f"{product_id}:{exc}")
        else:
            archived += 1
    print(
        json.dumps(
            {
                "cleanup_status": "passed" if not failed else "failed",
                "matched_count": len(targets),
                "archived_count": archived,
                "failed": failed,
            },
            ensure_ascii=False,
        )
    )
    return 0 if not failed else 1


def _request(
    base_url: str,
    method: str,
    path: str,
    timeout: float,
    *,
    token: str | None,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(urljoin(base_url.rstrip("/") + "/", path.lstrip("/")), method=method, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"status={exc.code} body={exc.read().decode('utf-8', errors='replace')}") from exc
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"expected object response, got={body!r}")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
