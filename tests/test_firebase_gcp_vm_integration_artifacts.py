from __future__ import annotations

from pathlib import Path


def test_firebase_frontend_env_example_exists() -> None:
    source = Path("apps/web/.env.firebase.example").read_text(encoding="utf-8")

    assert "NEXT_PUBLIC_API_BASE_URL=https://api.fit.aisoulfabrica.com" in source


def test_firebase_to_gcp_vm_runbook_exists() -> None:
    source = Path("docs/runbooks/firebase_hosting_to_gcp_vm_backend.md").read_text(encoding="utf-8")

    required_fragments = [
        "Firebase Hosting",
        "GCP VM",
        "NEXT_PUBLIC_API_BASE_URL",
        "CORS_ALLOWED_ORIGINS",
        "MESSAGING_PROVIDER=none",
        "api.fit.aisoulfabrica.com",
        "fit.aisoulfabrica.com",
        "firebase deploy --only hosting",
        "POST /api/try-on/jobs",
        "portable_remote_staging_ubuntu_22_04.md",
        "deploy_portable_runtime.sh .env.portable-remote-staging.local",
    ]

    for fragment in required_fragments:
        assert fragment in source
