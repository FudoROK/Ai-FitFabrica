"""Safe staging smoke checks that do not call paid AI providers."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class SmokeCheck:
    """One HTTP smoke check."""

    name: str
    target: str
    method: str
    path: str
    expected_statuses: set[int]
    requires_status_token: bool = False
    payload: dict[str, object] | None = None


@dataclass(frozen=True)
class SmokeResponse:
    """HTTP response captured by the smoke runner."""

    status_code: int
    body: dict[str, Any] | str


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Run no-billing staging smoke checks.")
    parser.add_argument("--api-base-url", default="https://api.fit.aisoulfabrica.com", help="Backend base URL.")
    parser.add_argument("--web-base-url", default="https://fit.aisoulfabrica.com", help="Frontend base URL.")
    parser.add_argument("--status-token", help="STATUS_ENDPOINT_TOKEN for /ready.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds.")
    parser.add_argument("--include-demo-request", action="store_true", help="Also write one public demo request.")
    parser.add_argument("--list", action="store_true", help="Print smoke matrix without HTTP requests.")
    return parser


def _check_matrix(*, include_demo_request: bool) -> list[SmokeCheck]:
    """Return the default no-billing staging smoke matrix."""

    checks = [
        SmokeCheck(name="backend_health", target="api", method="GET", path="/health", expected_statuses={200}),
        SmokeCheck(
            name="backend_ready",
            target="api",
            method="GET",
            path="/ready",
            expected_statuses={200},
            requires_status_token=True,
        ),
        SmokeCheck(name="workspace_bootstrap", target="api", method="GET", path="/api/workspace/bootstrap", expected_statuses={200}),
        SmokeCheck(name="auth_session", target="api", method="GET", path="/auth/session", expected_statuses={200}),
        SmokeCheck(
            name="auth_sign_in_fail_closed",
            target="api",
            method="POST",
            path="/auth/sign-in",
            expected_statuses={503},
            payload={"email": "smoke@example.com", "password": "not-a-real-password"},
        ),
        SmokeCheck(name="frontend_home", target="web", method="GET", path="/", expected_statuses={200}),
        SmokeCheck(name="frontend_business", target="web", method="GET", path="/business", expected_statuses={200}),
        SmokeCheck(name="frontend_b2c_for_you", target="web", method="GET", path="/for-you", expected_statuses={200}),
        SmokeCheck(name="frontend_pricing", target="web", method="GET", path="/pricing", expected_statuses={200}),
        SmokeCheck(name="frontend_login", target="web", method="GET", path="/login", expected_statuses={200}),
        SmokeCheck(name="frontend_contact", target="web", method="GET", path="/contact", expected_statuses={200}),
        SmokeCheck(name="frontend_workspace", target="web", method="GET", path="/workspace", expected_statuses={200}),
        SmokeCheck(name="frontend_b2c_try_on_new", target="web", method="GET", path="/workspace/try-on/new", expected_statuses={200}),
        SmokeCheck(name="frontend_b2c_similar_search", target="web", method="GET", path="/workspace/similar-search", expected_statuses={200}),
        SmokeCheck(name="frontend_b2c_outfit_builder", target="web", method="GET", path="/workspace/outfit-builder", expected_statuses={200}),
        SmokeCheck(name="frontend_b2b_business_catalog", target="web", method="GET", path="/workspace/business-catalog", expected_statuses={200}),
        SmokeCheck(name="frontend_b2b_product_card", target="web", method="GET", path="/workspace/product-card", expected_statuses={200}),
        SmokeCheck(name="frontend_b2b_content_package", target="web", method="GET", path="/workspace/content-package", expected_statuses={200}),
        SmokeCheck(name="frontend_b2b_business_profile", target="web", method="GET", path="/workspace/business-profile", expected_statuses={200}),
        SmokeCheck(name="frontend_admin_readiness", target="web", method="GET", path="/admin/readiness", expected_statuses={200}),
        SmokeCheck(name="frontend_b2b_admin_business_catalog", target="web", method="GET", path="/admin/business-catalog", expected_statuses={200}),
        SmokeCheck(name="frontend_b2b_admin_taxonomy", target="web", method="GET", path="/admin/taxonomy", expected_statuses={200}),
    ]
    if include_demo_request:
        checks.append(
            SmokeCheck(
                name="demo_request_write",
                target="api",
                method="POST",
                path="/demo-request",
                expected_statuses={200},
                payload={
                    "name": "Staging Smoke",
                    "email": "smoke@example.com",
                    "company": "AI FitFabrica",
                    "message": "No-billing staging smoke request.",
                },
            )
        )
    return checks


def _status_matches(response: SmokeResponse, expected_statuses: set[int]) -> bool:
    """Return whether a response has one allowed status."""

    return response.status_code in expected_statuses


def run_smoke(
    *,
    api_base_url: str,
    web_base_url: str,
    status_token: str | None,
    timeout: float,
    include_demo_request: bool,
) -> dict[str, object]:
    """Run the staging no-billing smoke matrix."""

    results: dict[str, dict[str, object]] = {}
    failed: list[str] = []
    for check in _check_matrix(include_demo_request=include_demo_request):
        if check.requires_status_token and not status_token:
            results[check.name] = {"status": "failed", "reason": "status_token_not_provided"}
            failed.append(check.name)
            continue
        response = _send_check(
            check=check,
            api_base_url=api_base_url,
            web_base_url=web_base_url,
            status_token=status_token,
            timeout=timeout,
        )
        passed = _status_matches(response, check.expected_statuses)
        if not passed:
            failed.append(check.name)
        results[check.name] = {
            "status": "passed" if passed else "failed",
            "status_code": response.status_code,
            "expected_statuses": sorted(check.expected_statuses),
            "body": response.body,
        }
    return {
        "smoke": "staging_no_billing",
        "readiness_status": "blocked" if failed else "ready",
        "failed_checks": failed,
        "checks": results,
    }


def _send_check(
    *,
    check: SmokeCheck,
    api_base_url: str,
    web_base_url: str,
    status_token: str | None,
    timeout: float,
) -> SmokeResponse:
    """Send one HTTP smoke request."""

    base_url = api_base_url if check.target == "api" else web_base_url
    headers = {"Accept": "application/json" if check.target == "api" else "text/html"}
    if check.requires_status_token and status_token:
        headers["X-Status-Token"] = status_token
    body: bytes | None = None
    if check.payload is not None:
        body = json.dumps(check.payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(
        url=urljoin(base_url.rstrip("/") + "/", check.path.lstrip("/")),
        method=check.method,
        data=body,
        headers=headers,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return SmokeResponse(status_code=response.status, body=_parse_body(response.read()))
    except HTTPError as exc:
        return SmokeResponse(status_code=exc.code, body=_parse_body(exc.read()))
    except URLError as exc:
        return SmokeResponse(status_code=0, body={"error": str(exc.reason)})


def _parse_body(raw: bytes) -> dict[str, Any] | str:
    """Parse JSON when possible and otherwise return a bounded text body."""

    text = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text[:500]
    return parsed if isinstance(parsed, dict) else text[:500]


def _list_payload(checks: list[SmokeCheck]) -> dict[str, object]:
    """Return a JSON-safe smoke matrix."""

    return {
        "smoke": "staging_no_billing",
        "checks": [
            {
                "name": check.name,
                "target": check.target,
                "method": check.method,
                "path": check.path,
                "expected_statuses": sorted(check.expected_statuses),
                "requires_status_token": check.requires_status_token,
            }
            for check in checks
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    args = _parser().parse_args(argv)
    checks = _check_matrix(include_demo_request=args.include_demo_request)
    if args.list:
        print(json.dumps(_list_payload(checks), ensure_ascii=False, sort_keys=True))
        return 0
    report = run_smoke(
        api_base_url=args.api_base_url,
        web_base_url=args.web_base_url,
        status_token=args.status_token,
        timeout=args.timeout,
        include_demo_request=args.include_demo_request,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["readiness_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
