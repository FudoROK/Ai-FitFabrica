"""Documentation guardrails for the Try-On sandbox API contract."""
from __future__ import annotations

from pathlib import Path


DOC_PATH = Path("docs/try-on-sandbox-api.md")


def test_try_on_sandbox_api_contract_doc_exists() -> None:
    """The sandbox API contract must stay documented before durable adapters."""
    source = DOC_PATH.read_text(encoding="utf-8")

    required_fragments = [
        "POST /api/try-on/jobs",
        "GET /api/jobs/{job_id}/status",
        "GET /api/jobs/{job_id}/result",
        "sandbox_lifecycle_mode",
        "not_ready",
        "job_failed",
        "No GCS",
        "No Firestore",
        "No Vertex",
    ]

    for fragment in required_fragments:
        assert fragment in source
