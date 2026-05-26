"""Documentation guardrails for the Try-On sandbox API contract."""
from __future__ import annotations

from pathlib import Path


DOC_PATH = Path("docs/try-on-sandbox-api.md")
ACTIVATION_DOC_PATH = Path("docs/try-on-durable-storage-activation.md")


def test_try_on_sandbox_api_contract_doc_exists() -> None:
    """The sandbox API contract must document storage and generation boundaries."""
    source = DOC_PATH.read_text(encoding="utf-8")

    required_fragments = [
        "POST /api/try-on/jobs",
        "GET /api/jobs/{job_id}/status",
        "GET /api/jobs/{job_id}/result",
        "sandbox_lifecycle_mode",
        "not_ready",
        "job_failed",
        "Storage Backend",
        "try_on_file_storage_backend=gcs",
        "try_on_job_repository_backend=firestore",
        "No live GCS or Firestore resource usage",
        "No Vertex",
    ]

    for fragment in required_fragments:
        assert fragment in source


def test_try_on_durable_storage_activation_doc_exists() -> None:
    """Durable storage activation must have an explicit operator document."""
    source = ACTIVATION_DOC_PATH.read_text(encoding="utf-8")

    required_fragments = [
        "Activation Boundary",
        "Required Environment",
        "IAM",
        "Dry Run",
        "Rollback",
        "TRY_ON_FILE_STORAGE_BACKEND=gcs",
        "TRY_ON_JOB_REPOSITORY_BACKEND=firestore",
        "No Vertex",
    ]

    for fragment in required_fragments:
        assert fragment in source
