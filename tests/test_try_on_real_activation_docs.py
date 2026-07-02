"""Documentation guardrails for real Vertex Try-On activation."""
from __future__ import annotations

from pathlib import Path


DOC_PATH = Path("docs/runbooks/try_on_real_activation.md")
ENV_PACK_PATH = Path("docs/runbooks/try_on_real_activation_staging.env.example")


def test_try_on_real_activation_doc_exists() -> None:
    """Real Vertex rollout must keep an explicit operator activation document."""
    source = DOC_PATH.read_text(encoding="utf-8")

    required_fragments = [
        "Activation Boundary",
        "Required Environment",
        "Fallback Policy",
        "Dry Run",
        "Rollback",
        "ENABLE_REAL_TRY_ON_GENERATION=true",
        "TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND",
        "scripts/try_on_real_activation_smoke.py",
        "--require-ready",
        "Staging Rollout Checklist",
        "/health",
        "No Silent Downgrade",
    ]

    for fragment in required_fragments:
        assert fragment in source


def test_try_on_real_activation_staging_env_pack_exists() -> None:
    """Staging rollout must keep a concrete env pack template for operators."""
    source = ENV_PACK_PATH.read_text(encoding="utf-8")

    required_fragments = [
        "ENVIRONMENT=staging",
        "TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on",
        "ENABLE_REAL_TRY_ON_GENERATION=true",
        "TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none",
        "OBJECT_STORAGE_BACKEND=s3",
        "POSTGRES_DSN=",
        "OPERATIONS_QUEUE_BACKEND=redis",
        "REDIS_URL=",
    ]

    for fragment in required_fragments:
        assert fragment in source
