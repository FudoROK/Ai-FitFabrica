"""Workflow handler registry for the portable worker runtime."""

from __future__ import annotations


def build_job_handlers() -> dict[str, object]:
    """Return the initial empty worker handler registry."""
    return {}
