"""Tests for portable media object-key naming."""

from __future__ import annotations

from src.adapters.storage.object_naming import build_media_object_key


def test_try_on_upload_key_uses_tenant_and_workflow_prefix() -> None:
    """Try-On uploads must use a deterministic tenant-scoped storage key."""
    key = build_media_object_key(
        tenant_id="public",
        workflow="try-on",
        job_id="job_123",
        role="human_photo",
        filename="Human Photo!!.jpg",
    )

    assert key == "fitfabrica/tenants/public/try-on/job_123/human_photo/Human-Photo-.jpg"


def test_filename_is_safely_normalized() -> None:
    """Unsafe filenames must collapse to the upload role fallback."""
    key = build_media_object_key(
        tenant_id="public",
        workflow="try-on",
        job_id="job_123",
        role="garment_photo",
        filename="  ###  ",
    )

    assert key.endswith("/garment_photo/garment_photo")
