"""HTTP smoke test for the B2B business catalog staging surface."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@dataclass(frozen=True)
class SmokeResponse:
    status_code: int
    body: dict[str, Any] | str


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run B2B business catalog staging smoke.")
    parser.add_argument("--base-url", default="https://api.fit.aisoulfabrica.com", help="Backend base URL.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds.")
    parser.add_argument("--admin-role", default="catalog_admin", help="Admin role header for admin gate check.")
    parser.add_argument("--admin-id", default="business-catalog-smoke", help="Admin actor id header for admin gate check.")
    parser.add_argument(
        "--require-admin-enabled",
        action="store_true",
        help="Fail if admin business catalog API is disabled.",
    )
    return parser


def _json_request(
    *,
    base_url: str,
    method: str,
    path: str,
    timeout: float,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> SmokeResponse:
    request_headers = {"Accept": "application/json", **(headers or {})}
    body: bytes | None = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    return _send(base_url=base_url, method=method, path=path, timeout=timeout, body=body, headers=request_headers)


def _multipart_request(
    *,
    base_url: str,
    path: str,
    timeout: float,
    fields: dict[str, str] | None,
    file_field: str,
    filename: str,
    content_type: str,
    content: bytes,
    headers: dict[str, str] | None = None,
) -> SmokeResponse:
    boundary = f"----fitfabrica-smoke-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in (fields or {}).items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    chunks.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    request_headers = {
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        **(headers or {}),
    }
    return _send(
        base_url=base_url,
        method="POST",
        path=path,
        timeout=timeout,
        body=b"".join(chunks),
        headers=request_headers,
    )


def _send(
    *,
    base_url: str,
    method: str,
    path: str,
    timeout: float,
    body: bytes | None,
    headers: dict[str, str],
) -> SmokeResponse:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    request = Request(url=url, method=method, data=body, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return SmokeResponse(status_code=response.status, body=_parse_body(raw))
    except HTTPError as exc:
        return SmokeResponse(status_code=exc.code, body=_parse_body(exc.read()))
    except URLError as exc:
        raise RuntimeError(f"Cannot reach {url}: {exc.reason}") from exc


def _parse_body(raw: bytes) -> dict[str, Any] | str:
    text = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    return parsed if isinstance(parsed, dict) else text


def _expect(response: SmokeResponse, expected_status: int, label: str) -> dict[str, Any]:
    if response.status_code != expected_status:
        raise RuntimeError(f"{label} failed: status={response.status_code} body={response.body}")
    if not isinstance(response.body, dict):
        raise RuntimeError(f"{label} failed: expected JSON object, got={response.body!r}")
    print(f"{label}=ok status={response.status_code}")
    return response.body


def _catalog_csv() -> bytes:
    return (
        "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
        "Smoke shirt,shirt,14990,KZT,KZ,Almaty,in_stock,https://example.com/smoke-shirt,Almaty;Astana\n"
    ).encode("utf-8")


def run_smoke(*, base_url: str, timeout: float, admin_role: str, admin_id: str, require_admin_enabled: bool) -> int:
    print(f"business_catalog_staging_smoke base_url={base_url}")
    health = _expect(_json_request(base_url=base_url, method="GET", path="/health", timeout=timeout), 200, "health")
    print(f"health_status={health.get('status', 'unknown')}")

    merchant_payload = {
        "display_name": "Smoke Test Store",
        "country_code": "KZ",
        "city": "Almaty",
        "contact_email": "smoke@example.com",
    }
    _expect(
        _json_request(base_url=base_url, method="POST", path="/api/business/merchant", timeout=timeout, payload=merchant_payload),
        200,
        "merchant_save",
    )
    _expect(_json_request(base_url=base_url, method="GET", path="/api/business/merchant", timeout=timeout), 200, "merchant_get")

    product_body = _expect(
        _json_request(
            base_url=base_url,
            method="POST",
            path="/api/business/products",
            timeout=timeout,
            payload={
                "title": "Smoke white shirt",
                "category": "shirt",
                "country_code": "KZ",
                "city": "Almaty",
                "offer": {
                    "price_amount": "14990",
                    "currency": "KZT",
                    "availability": "in_stock",
                    "product_url": "https://example.com/smoke-white-shirt",
                    "delivery_regions": ["Almaty", "Astana"],
                },
            },
        ),
        200,
        "product_create",
    )
    product_id = product_body["product"]["product_id"]
    _expect(_json_request(base_url=base_url, method="GET", path="/api/business/products", timeout=timeout), 200, "product_list")

    _expect(
        _multipart_request(
            base_url=base_url,
            path=f"/api/business/products/{product_id}/images",
            timeout=timeout,
            fields={"role": "primary", "sort_order": "0"},
            file_field="file",
            filename="smoke.png",
            content_type="image/png",
            content=PNG_1X1,
            headers={"Idempotency-Key": f"smoke-image-{product_id}"},
        ),
        200,
        "image_upload",
    )
    _expect(
        _json_request(
            base_url=base_url,
            method="POST",
            path=f"/api/business/products/{product_id}/submit",
            timeout=timeout,
            headers={"Idempotency-Key": f"smoke-submit-{product_id}"},
        ),
        200,
        "product_submit",
    )

    import_body = _expect(
        _multipart_request(
            base_url=base_url,
            path="/api/business/catalog-imports",
            timeout=timeout,
            fields=None,
            file_field="file",
            filename="smoke-products.csv",
            content_type="text/csv",
            content=_catalog_csv(),
            headers={"Idempotency-Key": f"smoke-import-{uuid.uuid4().hex}"},
        ),
        200,
        "csv_import",
    )
    import_id = import_body["import_job"]["import_id"]
    _expect(
        _json_request(base_url=base_url, method="GET", path=f"/api/business/catalog-imports/{import_id}", timeout=timeout),
        200,
        "csv_import_get",
    )
    _expect(
        _json_request(base_url=base_url, method="GET", path=f"/api/business/catalog-imports/{import_id}/errors", timeout=timeout),
        200,
        "csv_import_errors",
    )

    admin_response = _json_request(
        base_url=base_url,
        method="GET",
        path="/api/admin/business-catalog/merchants/tiers",
        timeout=timeout,
        headers={"X-Fitfabrica-Admin-Role": admin_role, "X-Fitfabrica-Admin-Id": admin_id},
    )
    if admin_response.status_code == 200:
        print("admin_tier_gate=enabled status=200")
    elif admin_response.status_code == 404 and not require_admin_enabled:
        print("admin_tier_gate=disabled status=404")
    else:
        raise RuntimeError(f"admin_tier_gate failed: status={admin_response.status_code} body={admin_response.body}")

    print("smoke_status=passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return run_smoke(
            base_url=args.base_url,
            timeout=args.timeout,
            admin_role=args.admin_role,
            admin_id=args.admin_id,
            require_admin_enabled=args.require_admin_enabled,
        )
    except RuntimeError as exc:
        print(f"smoke_status=failed error={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
