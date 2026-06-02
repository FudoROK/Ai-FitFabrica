"""Deterministic object-key naming for portable media storage."""

from __future__ import annotations

import re


def normalize_storage_filename(*, filename: str, fallback: str) -> str:
    """Return a storage-safe filename while preserving readable intent."""
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-")
    return normalized or fallback


def build_media_object_key(
    *,
    tenant_id: str,
    workflow: str,
    job_id: str,
    role: str,
    filename: str,
    root_prefix: str = "fitfabrica",
) -> str:
    """Build a stable tenant-scoped object key for binary workflow artifacts."""
    safe_filename = normalize_storage_filename(filename=filename, fallback=role)
    return "/".join(
        [
            root_prefix.strip("/"),
            "tenants",
            tenant_id,
            workflow,
            job_id,
            role,
            safe_filename,
        ]
    )
