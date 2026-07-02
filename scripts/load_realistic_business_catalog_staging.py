"""Load the realistic B2B catalog test pack into staging through real HTTP APIs."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HttpResponse:
    """Small typed response wrapper for staging API calls."""

    status_code: int
    body: dict[str, Any] | str


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load realistic business catalog test data into staging.")
    parser.add_argument("--base-url", default="https://api.fit.aisoulfabrica.com")
    parser.add_argument("--pack-dir", required=True, help="Path to the _import_ready test pack directory.")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--admin-role", default="catalog_admin")
    parser.add_argument("--admin-id", default="realistic-catalog-loader")
    parser.add_argument(
        "--admin-token-env",
        default="FITFABRICA_ADMIN_API_TOKEN",
        help="Environment variable containing the staging admin bearer token.",
    )
    parser.add_argument("--skip-admin-approve", action="store_true")
    parser.add_argument("--skip-similar-search", action="store_true")
    parser.add_argument(
        "--allow-category-blocks",
        action="store_true",
        help="Allow category mismatches/uncertain products when validating a deliberately imperfect test pack.",
    )
    parser.add_argument("--poll-index-seconds", type=int, default=120)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    pack_dir = Path(args.pack_dir)
    csv_path = pack_dir / "business_catalog_import_ready.csv"
    manifest_path = pack_dir / "business_catalog_image_upload_manifest.csv"
    image_dir = pack_dir / "images"

    rows = _read_csv(csv_path)
    manifest = _read_manifest(manifest_path)
    _validate_pack(rows=rows, manifest=manifest, image_dir=image_dir)

    print(f"load_catalog base_url={args.base_url}")
    _expect(_json_request(args.base_url, "GET", "/health", args.timeout), 200, "health")

    _expect(
        _json_request(
            args.base_url,
            "POST",
            "/api/business/merchant",
            args.timeout,
            payload={
                "display_name": "FitFabrica Realistic Test Store",
                "legal_name": "FitFabrica Realistic Test Store",
                "country_code": "KZ",
                "city": "Almaty",
                "contact_email": "realistic-test@example.com",
                "website_url": "https://example.com/fitfabrica-test-store",
            },
        ),
        200,
        "merchant_upsert",
    )

    import_body = _expect(
        _multipart_request(
            args.base_url,
            "/api/business/catalog-imports",
            args.timeout,
            file_field="file",
            filename=csv_path.name,
            content_type="text/csv",
            content=csv_path.read_bytes(),
            fields=None,
            headers={"Idempotency-Key": f"realistic-import-{uuid.uuid4().hex}"},
        ),
        200,
        "catalog_import",
    )
    import_job = import_body["import_job"]
    print(
        "catalog_import_summary="
        f"total={import_job['total_rows']} accepted={import_job['accepted_rows']} rejected={import_job['rejected_rows']}"
    )
    if import_job["accepted_rows"] != len(rows) or import_job["rejected_rows"] != 0:
        raise RuntimeError(f"Unexpected import result: {import_job}")

    products = _expect(_json_request(args.base_url, "GET", "/api/business/products", args.timeout), 200, "product_list")[
        "products"
    ]
    imported_products = _match_imported_products(rows=rows, products=products)
    print(f"matched_products={len(imported_products)}")

    for index, row in enumerate(rows):
        product = imported_products[row["title"]]
        image_name = manifest[row["title"]]["image_filename"]
        image_path = image_dir / image_name
        _expect(
            _multipart_request(
                args.base_url,
                f"/api/business/products/{product['product_id']}/images",
                args.timeout,
                file_field="file",
                filename=image_name,
                content_type="image/png",
                content=image_path.read_bytes(),
                fields={"role": "primary", "sort_order": str(index)},
                headers={"Idempotency-Key": f"realistic-image-{product['product_id']}-{image_name}"},
            ),
            200,
            f"image_upload[{index + 1:02d}]",
        )
        _expect(
            _json_request(
                args.base_url,
                "POST",
                f"/api/business/products/{product['product_id']}/submit",
                args.timeout,
                headers={"Idempotency-Key": f"realistic-submit-{product['product_id']}"},
            ),
            200,
            f"product_submit[{index + 1:02d}]",
        )

    if not args.skip_admin_approve:
        approval = _approve_pending(args=args, expected_product_count=len(imported_products))
        _poll_indexed(
            base_url=args.base_url,
            timeout=args.timeout,
            product_ids=approval.approved_product_ids,
            max_seconds=args.poll_index_seconds,
        )

    if not args.skip_similar_search:
        _run_similar_search_probe(args=args, row=rows[0])

    print("load_catalog_status=passed")
    return 0


@dataclass(frozen=True)
class CategoryValidationSummary:
    processed_count: int
    matched_product_ids: list[str]
    blocked_product_ids: list[str]


@dataclass(frozen=True)
class ApprovalSummary:
    approved_product_ids: list[str]
    blocked_product_ids: list[str]


def _approve_pending(*, args: argparse.Namespace, expected_product_count: int) -> ApprovalSummary:
    headers = _admin_headers(args)
    pending = _json_request(
        args.base_url,
        "GET",
        "/api/admin/business-catalog/products/pending",
        args.timeout,
        headers=headers,
    )
    if pending.status_code == 404:
        raise RuntimeError("Admin business catalog API is disabled on staging; enable it before approval.")
    _expect(pending, 200, "admin_pending")
    validation = _validate_pending_categories(args=args, headers=headers, expected_product_count=expected_product_count)
    if validation.blocked_product_ids and not args.allow_category_blocks:
        raise RuntimeError(
            "Category validation blocked "
            f"{len(validation.blocked_product_ids)} products; fix the pack or pass --allow-category-blocks."
        )
    approved_product_ids = _approve_matched_pending(
        args=args,
        headers=headers,
        expected_approved_count=len(validation.matched_product_ids),
    )
    return ApprovalSummary(approved_product_ids=approved_product_ids, blocked_product_ids=validation.blocked_product_ids)


def _admin_headers(args: argparse.Namespace) -> dict[str, str]:
    token = os.environ.get(args.admin_token_env, "").strip()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {"X-Fitfabrica-Admin-Role": args.admin_role, "X-Fitfabrica-Admin-Id": args.admin_id}


def _validate_pending_categories(
    *,
    args: argparse.Namespace,
    headers: dict[str, str],
    expected_product_count: int,
) -> CategoryValidationSummary:
    processed_total = 0
    failed_total = 0
    matched_product_ids: list[str] = []
    blocked_product_ids: list[str] = []
    while processed_total < expected_product_count:
        body = _expect(
            _json_request(
                args.base_url,
                "POST",
                "/api/admin/business-catalog/products/category-validation/run-batch",
                args.timeout,
                payload={"limit": 25},
                headers=headers,
            ),
            200,
            "admin_category_validation_batch",
        )
        result = body["result"]
        processed_count = int(result["processed_count"])
        processed_total += processed_count
        failed_total += int(result["failed_count"])
        for item in result.get("items", []):
            product = item.get("product") or {}
            product_id = item.get("product_id")
            validation_status = product.get("category_validation_status")
            if validation_status == "matched":
                matched_product_ids.append(product_id)
            elif validation_status in {"mismatch", "uncertain"}:
                blocked_product_ids.append(product_id)
        print(
            "category_validation_summary="
            f"processed_total={processed_total} validated_batch={result['validated_count']} "
            f"matched_total={len(matched_product_ids)} blocked_total={len(blocked_product_ids)} failed_total={failed_total}"
        )
        if processed_count == 0:
            break
    if processed_total < expected_product_count:
        raise RuntimeError(f"Category validation processed only {processed_total}/{expected_product_count} products.")
    if failed_total:
        raise RuntimeError(f"Category validation failed for {failed_total} products.")
    return CategoryValidationSummary(
        processed_count=processed_total,
        matched_product_ids=matched_product_ids,
        blocked_product_ids=blocked_product_ids,
    )


def _approve_matched_pending(
    *,
    args: argparse.Namespace,
    headers: dict[str, str],
    expected_approved_count: int,
) -> list[str]:
    approved_total = 0
    failed_total = 0
    approved_product_ids: list[str] = []
    while approved_total < expected_approved_count:
        body = _expect(
            _json_request(
                args.base_url,
                "POST",
                "/api/admin/business-catalog/products/approve-matched-batch",
                args.timeout,
                payload={"limit": 25},
                headers=headers,
            ),
            200,
            "admin_approve_matched_batch",
        )
        result = body["result"]
        processed_count = int(result["processed_count"])
        approved_total += int(result["approved_count"])
        failed_total += int(result["failed_count"])
        approved_product_ids.extend(
            item["product_id"]
            for item in result.get("items", [])
            if item.get("status") == "approved"
        )
        print(
            "approve_matched_summary="
            f"processed_batch={processed_count} approved_total={approved_total} failed_total={failed_total}"
        )
        if processed_count == 0:
            break
    if approved_total < expected_approved_count:
        raise RuntimeError(f"Approved only {approved_total}/{expected_approved_count} matched products.")
    if failed_total:
        raise RuntimeError(f"Approval failed for {failed_total} products.")
    return approved_product_ids


def _poll_indexed(*, base_url: str, timeout: float, product_ids: list[str], max_seconds: int) -> None:
    if not product_ids:
        print("indexed_products=0")
        return
    deadline = time.monotonic() + max_seconds
    wanted = set(product_ids)
    last_statuses: dict[str, str] = {}
    while time.monotonic() < deadline:
        products = _expect(_json_request(base_url, "GET", "/api/business/products", timeout), 200, "index_poll")[
            "products"
        ]
        statuses = {
            product["product_id"]: product.get("search_index_status", "unknown")
            for product in products
            if product["product_id"] in wanted
        }
        last_statuses = statuses
        if statuses and all(status == "indexed" for status in statuses.values()):
            print(f"indexed_products={len(statuses)}")
            return
        time.sleep(5)
    raise RuntimeError(f"Products were not indexed before timeout: {last_statuses}")


def _run_similar_search_probe(*, args: argparse.Namespace, row: dict[str, str]) -> None:
    body = _expect(
        _json_request(
            args.base_url,
            "POST",
            "/api/similar-search",
            args.timeout,
            payload={
                "source_type": "text",
                "query_text": row["title"],
                "category": row["category"],
                "limit": 10,
                "user_country_code": "KZ",
                "user_city": "Almaty",
            },
        ),
        200,
        "similar_search_structured_probe",
    )
    results = body.get("results", [])
    print(f"similar_search_results={len(results)}")
    if not results:
        raise RuntimeError("Similar Search returned no results for the realistic catalog probe.")
    first = results[0]
    print(
        "similar_search_top="
        f"title={first.get('title')} city={first.get('city')} score={first.get('similarity_score')}"
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {row["title"]: row for row in rows}


def _validate_pack(*, rows: list[dict[str, str]], manifest: dict[str, dict[str, str]], image_dir: Path) -> None:
    if not rows:
        raise RuntimeError("Import CSV has no rows.")
    for row in rows:
        title = row["title"]
        if title not in manifest:
            raise RuntimeError(f"Missing manifest row for title: {title}")
        image_path = image_dir / manifest[title]["image_filename"]
        if not image_path.exists():
            raise RuntimeError(f"Missing image: {image_path}")
        if image_path.stat().st_size > 10 * 1024 * 1024:
            raise RuntimeError(f"Image exceeds 10 MB: {image_path}")
        expected_category = _expected_category_from_image_name(image_path.name)
        declared_category = (row.get("category") or "").strip().casefold()
        if expected_category is not None and declared_category != expected_category:
            raise RuntimeError(
                "Category mismatch: "
                f"title={title!r} declared={declared_category!r} image={image_path.name!r} expected={expected_category!r}"
            )


def _expected_category_from_image_name(filename: str) -> str | None:
    """Infer expected catalog category from controlled realistic-pack filenames."""

    normalized = filename.strip().casefold().replace("-", "_")
    tokens = [token for token in normalized.replace(".", "_").split("_") if token]
    if "tshirt" in tokens or "tee" in tokens or "longsleeve" in tokens:
        return "tshirt"
    if "dress" in normalized:
        return "dress"
    if "skirt" in normalized:
        return "skirt"
    if any(token in normalized for token in ("coat", "jacket", "outerwear", "blazer")):
        return "outerwear"
    if any(token in normalized for token in ("pants", "jeans", "trouser")):
        return "pants"
    if "shirt" in normalized:
        return "shirt"
    return None


def _match_imported_products(*, rows: list[dict[str, str]], products: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    matched: dict[str, dict[str, Any]] = {}
    for row in rows:
        title = row["title"]
        candidates = [
            product
            for product in products
            if product.get("title") == title
            and product.get("source_type") == "csv_import"
            and product.get("status") == "draft"
        ]
        if not candidates:
            raise RuntimeError(f"Imported product not found for title: {title}")
        candidates.sort(key=lambda product: str(product.get("created_at", "")), reverse=True)
        matched[title] = candidates[0]
    return matched


def _json_request(
    base_url: str,
    method: str,
    path: str,
    timeout: float,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    request_headers = {"Accept": "application/json", **(headers or {})}
    body: bytes | None = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    return _send(base_url, method, path, timeout, body=body, headers=request_headers)


def _multipart_request(
    base_url: str,
    path: str,
    timeout: float,
    *,
    fields: dict[str, str] | None,
    file_field: str,
    filename: str,
    content_type: str,
    content: bytes,
    headers: dict[str, str] | None,
) -> HttpResponse:
    boundary = f"----fitfabrica-realistic-{uuid.uuid4().hex}"
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
    return _send(base_url, "POST", path, timeout, body=b"".join(chunks), headers=request_headers)


def _send(
    base_url: str,
    method: str,
    path: str,
    timeout: float,
    *,
    body: bytes | None,
    headers: dict[str, str],
) -> HttpResponse:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    request = Request(url=url, method=method, data=body, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            return HttpResponse(status_code=response.status, body=_parse_body(response.read()))
    except HTTPError as exc:
        return HttpResponse(status_code=exc.code, body=_parse_body(exc.read()))
    except URLError as exc:
        raise RuntimeError(f"Cannot reach {url}: {exc.reason}") from exc


def _parse_body(raw: bytes) -> dict[str, Any] | str:
    text = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    return parsed if isinstance(parsed, dict) else text


def _expect(response: HttpResponse, expected_status: int, label: str) -> dict[str, Any]:
    if response.status_code != expected_status:
        raise RuntimeError(f"{label} failed: status={response.status_code} body={response.body}")
    if not isinstance(response.body, dict):
        raise RuntimeError(f"{label} failed: expected JSON object, got={response.body!r}")
    print(f"{label}=ok status={response.status_code}")
    return response.body


if __name__ == "__main__":
    raise SystemExit(main())
