"""Run deployed HTTP/worker Try-On smoke against a live backend URL."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import httpx


def _parser() -> argparse.ArgumentParser:
    """Build CLI parser for deployed Try-On HTTP smoke."""
    parser = argparse.ArgumentParser(description="Run deployed HTTP/worker Try-On smoke.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080", help="Backend base URL.")
    parser.add_argument("--human", type=Path, required=True, help="Human/person image.")
    parser.add_argument("--garment", type=Path, required=True, help="Garment/product image.")
    parser.add_argument("--timeout-seconds", type=float, default=180.0, help="Polling timeout.")
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0, help="Polling interval.")
    parser.add_argument(
        "--sandbox-lifecycle-mode",
        default="complete",
        choices=["complete", "pending", "analysis_only", "failed", "repair_acceptance"],
        help="Lifecycle mode sent to the deployed Try-On API.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/try_on_http_worker_live_smoke_<timestamp>.jsonl.",
    )
    parser.add_argument("--require-pass", action="store_true", help="Exit non-zero when smoke validation fails.")
    return parser


def _run_smoke(
    *,
    base_url: str,
    human: Path,
    garment: Path,
    timeout_seconds: float,
    poll_interval_seconds: float,
    sandbox_lifecycle_mode: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Create one Try-On job through HTTP and poll until final result."""
    rows: list[dict[str, object]] = []
    with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        created = _create_job(
            client=client,
            base_url=base_url,
            human=human,
            garment=garment,
            sandbox_lifecycle_mode=sandbox_lifecycle_mode,
        )
        rows.append({"stage": "create_job", **created})
        job_id = str(created["job_id"])
        status_url = _absolute_url(base_url, str(created["status_url"]))
        result_url = _absolute_url(base_url, str(created["result_url"]))
        final_status = _poll_status(
            client=client,
            status_url=status_url,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        rows.append({"stage": "poll_status", **final_status})
        result = client.get(result_url)
        result.raise_for_status()
        result_payload = result.json()
        rows.append({"stage": "result", "payload": result_payload})

    quality_report = result_payload.get("result", {}).get("quality_report", {}) if isinstance(result_payload, dict) else {}
    quality_verdict = quality_report.get("verdict") if isinstance(quality_report, dict) else None
    final_status_value = final_status.get("status")
    passed = final_status_value == "completed" and quality_verdict == "pass"
    summary = {
        "passed": passed,
        "job_id": job_id,
        "final_status": final_status_value,
        "quality_verdict": quality_verdict,
        "result_status": result_payload.get("status") if isinstance(result_payload, dict) else None,
    }
    return rows, summary


def _create_job(
    *,
    client,
    base_url: str,
    human: Path,
    garment: Path,
    sandbox_lifecycle_mode: str,
) -> dict[str, object]:
    """POST one Try-On job with multipart files."""
    if not human.is_file():
        raise ValueError(f"human image does not exist: {human}")
    if not garment.is_file():
        raise ValueError(f"garment image does not exist: {garment}")
    url = _absolute_url(base_url, "/api/try-on/jobs")
    with human.open("rb") as human_handle, garment.open("rb") as garment_handle:
        response = client.post(
            url,
            files={
                "human_photo": (human.name, human_handle, _content_type(human)),
                "garment_photo": (garment.name, garment_handle, _content_type(garment)),
            },
            data={"sandbox_lifecycle_mode": sandbox_lifecycle_mode},
        )
    response.raise_for_status()
    payload = response.json()
    for key in ("job_id", "status_url", "result_url"):
        if key not in payload:
            raise RuntimeError(f"create_job response missing {key}")
    return payload


def _poll_status(
    *,
    client,
    status_url: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, object]:
    """Poll job status until completed/failed or timeout."""
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, object] = {}
    while time.monotonic() < deadline:
        response = client.get(status_url)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("status response is not an object")
        last_payload = payload
        status = payload.get("status")
        if status in {"completed", "failed"}:
            return payload
        time.sleep(poll_interval_seconds)
    raise TimeoutError(f"Try-On job did not finish before timeout. Last status: {last_payload}")


def _content_type(path: Path) -> str:
    """Return supported upload content type from filename."""
    guessed, _encoding = mimetypes.guess_type(path.name)
    if guessed in {"image/jpeg", "image/png", "image/webp"}:
        return guessed
    raise ValueError(f"unsupported image type: {path.name}")


def _absolute_url(base_url: str, path_or_url: str) -> str:
    """Build absolute URL from base and route response path."""
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    return urljoin(base_url.rstrip("/") + "/", path_or_url.lstrip("/"))


def _output_path(path: Path | None) -> Path:
    """Resolve JSONL output path."""
    if path is not None:
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"try_on_http_worker_live_smoke_{timestamp}.jsonl"


def _write_jsonl(*, output_path: Path, rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    """Write all smoke rows and one summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({"type": "stage", **row}, ensure_ascii=False) + "\n")
        handle.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Run the deployed HTTP/worker smoke CLI."""
    args = _parser().parse_args(argv)
    try:
        rows, summary = _run_smoke(
            base_url=args.base_url,
            human=args.human,
            garment=args.garment,
            timeout_seconds=args.timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
            sandbox_lifecycle_mode=args.sandbox_lifecycle_mode,
        )
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, rows=rows, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("try_on_http_worker_live_smoke_status=error")
        print(f"error={exc}")
        return 1

    print("try_on_http_worker_live_smoke_status=completed")
    print(f"output={output_path}")
    print(f"passed={summary['passed']}")
    print(f"job_id={summary['job_id']}")
    print(f"final_status={summary['final_status']}")
    print(f"quality_verdict={summary['quality_verdict']}")
    if args.require_pass and summary["passed"] is not True:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
