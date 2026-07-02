"""Documentation guardrails for the Try-On sandbox API contract."""
from __future__ import annotations

from pathlib import Path


DOC_PATH = Path("docs/runbooks/try_on_sandbox_api.md")
ACTIVATION_DOC_PATH = Path("docs/runbooks/try_on_durable_storage_activation.md")


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
        "object_storage_backend=s3",
        "portable SQL infrastructure",
        "try_on_generation_backend=sandbox_fake|provider_runtime",
        "try_on_quality_verifier_backend=deterministic|model_backed",
        "try_on_repair_backend=deterministic|provider_runtime",
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
        "OBJECT_STORAGE_BACKEND=s3",
        "OBJECT_STORAGE_BUCKET_NAME",
        "POSTGRES_DSN",
        "No Vertex",
    ]

    for fragment in required_fragments:
        assert fragment in source
