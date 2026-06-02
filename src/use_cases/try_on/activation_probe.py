"""Dry-run readiness probe for real Vertex Try-On activation."""

from __future__ import annotations

import importlib.util
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TryOnActivationCheck(BaseModel):
    """One operator-facing readiness check for real Try-On activation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    status: Literal["passed", "failed", "warning", "inactive"]
    message: str = Field(min_length=1)


class TryOnActivationProbeResult(BaseModel):
    """Aggregated dry-run readiness result for the real Vertex Try-On path."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(min_length=1)
    activation_enabled: bool
    readiness_status: Literal["ready", "blocked", "inactive"]
    fallback_backend: str = Field(min_length=1)
    checks: list[TryOnActivationCheck] = Field(default_factory=list)


def probe_try_on_real_activation(settings) -> TryOnActivationProbeResult:
    """Evaluate whether the backend is ready to enable the real Vertex Try-On path."""
    backend = getattr(settings, "try_on_generation_backend", "sandbox_fake")
    activation_enabled = bool(getattr(settings, "enable_real_try_on_generation", False))
    fallback_backend = getattr(settings, "try_on_vertex_failure_fallback_backend", "none")
    environment = str(getattr(settings, "environment", "prod") or "prod").strip().lower()
    checks: list[TryOnActivationCheck] = []

    if backend != "vertex_virtual_try_on" and not activation_enabled:
        checks.append(
            TryOnActivationCheck(
                name="activation_request",
                status="inactive",
                message="Real Vertex Try-On is not requested in the current settings snapshot.",
            )
        )
        return TryOnActivationProbeResult(
            backend=backend,
            activation_enabled=activation_enabled,
            readiness_status="inactive",
            fallback_backend=fallback_backend,
            checks=checks,
        )

    checks.append(
        _check(
            name="generation_backend",
            condition=backend == "vertex_virtual_try_on",
            ok_message="TRY_ON_GENERATION_BACKEND selects the dedicated Vertex Virtual Try-On path.",
            fail_message="TRY_ON_GENERATION_BACKEND must be vertex_virtual_try_on for real activation.",
        )
    )
    checks.append(
        _check(
            name="activation_flag",
            condition=activation_enabled,
            ok_message="ENABLE_REAL_TRY_ON_GENERATION is enabled.",
            fail_message="ENABLE_REAL_TRY_ON_GENERATION must be true for real activation.",
        )
    )
    checks.append(
        _check(
            name="object_storage_backend",
            condition=getattr(settings, "object_storage_backend", "in_memory") == "s3",
            ok_message="OBJECT_STORAGE_BACKEND is set to s3 for durable result artifacts.",
            fail_message="OBJECT_STORAGE_BACKEND must be s3 for real activation.",
        )
    )
    checks.append(
        _check(
            name="postgres_dsn",
            condition=_has_real_value(getattr(settings, "postgres_dsn", None)),
            ok_message="POSTGRES_DSN is configured for durable workflow state.",
            fail_message="POSTGRES_DSN must be configured for real activation.",
        )
    )
    checks.append(
        _check(
            name="operations_queue_backend",
            condition=getattr(settings, "operations_queue_backend", "in_memory") == "redis",
            ok_message="OPERATIONS_QUEUE_BACKEND is set to redis for worker dispatch.",
            fail_message="OPERATIONS_QUEUE_BACKEND must be redis for real activation.",
        )
    )
    checks.append(
        _check(
            name="redis_url",
            condition=_has_real_value(getattr(settings, "redis_url", None)),
            ok_message="REDIS_URL is configured for queue and short-lived coordination.",
            fail_message="REDIS_URL must be configured for real activation.",
        )
    )
    checks.append(
        _check(
            name="vertex_project",
            condition=_has_real_value(getattr(settings, "vertex_project", None)),
            ok_message="VERTEX_PROJECT is configured for Vertex Virtual Try-On.",
            fail_message="VERTEX_PROJECT must be configured for real activation.",
        )
    )
    checks.append(
        _check(
            name="vertex_model",
            condition=_has_real_value(getattr(settings, "vertex_virtual_try_on_model", None)),
            ok_message="VERTEX_VIRTUAL_TRY_ON_MODEL is configured.",
            fail_message="VERTEX_VIRTUAL_TRY_ON_MODEL must be configured for real activation.",
        )
    )
    checks.append(
        _check(
            name="object_storage_access_key_id",
            condition=_has_real_value(getattr(settings, "object_storage_access_key_id", None)),
            ok_message="OBJECT_STORAGE_ACCESS_KEY_ID looks populated with a non-placeholder value.",
            fail_message="OBJECT_STORAGE_ACCESS_KEY_ID must be replaced with a real HMAC access key.",
        )
    )
    checks.append(
        _check(
            name="object_storage_secret_access_key",
            condition=_has_real_value(getattr(settings, "object_storage_secret_access_key", None)),
            ok_message="OBJECT_STORAGE_SECRET_ACCESS_KEY looks populated with a non-placeholder value.",
            fail_message="OBJECT_STORAGE_SECRET_ACCESS_KEY must be replaced with a real HMAC secret.",
        )
    )
    checks.append(
        _check(
            name="google_genai_sdk",
            condition=importlib.util.find_spec("google.genai") is not None,
            ok_message="google-genai SDK is importable for the Vertex client wrapper.",
            fail_message="google-genai SDK must be installed before real activation.",
        )
    )
    checks.append(
        _check(
            name="google_genai_types",
            condition=importlib.util.find_spec("google.genai.types") is not None,
            ok_message="google-genai typed request payload support is importable.",
            fail_message="google-genai typed request payload support must be installed before real activation.",
        )
    )
    checks.append(_fallback_check(fallback_backend=fallback_backend, environment=environment, settings=settings))

    readiness_status: Literal["ready", "blocked", "inactive"] = (
        "blocked" if any(check.status == "failed" for check in checks) else "ready"
    )
    return TryOnActivationProbeResult(
        backend=backend,
        activation_enabled=activation_enabled,
        readiness_status=readiness_status,
        fallback_backend=fallback_backend,
        checks=checks,
    )


def _check(*, name: str, condition: bool, ok_message: str, fail_message: str) -> TryOnActivationCheck:
    """Build one pass/fail readiness check."""
    return TryOnActivationCheck(
        name=name,
        status="passed" if condition else "failed",
        message=ok_message if condition else fail_message,
    )


def _fallback_check(*, fallback_backend: str, environment: str, settings) -> TryOnActivationCheck:
    """Build the rollout fallback policy readiness check."""
    if fallback_backend == "none":
        return TryOnActivationCheck(
            name="fallback_policy",
            status="passed",
            message="TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none keeps the real path on explicit fail-fast policy.",
        )
    if environment not in {"prod", "production", "staging", "stage", "preprod", "preproduction"}:
        return TryOnActivationCheck(
            name="fallback_policy",
            status="warning",
            message=(
                "TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND allows downgrade behavior. "
                "This is acceptable only for controlled non-production rollout."
            ),
        )
    if bool(getattr(settings, "allow_unsafe_try_on_vertex_fallback_in_production", False)):
        return TryOnActivationCheck(
            name="fallback_policy",
            status="warning",
            message=(
                "Production-like fallback is explicitly overridden through "
                "ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION=true."
            ),
        )
    return TryOnActivationCheck(
        name="fallback_policy",
        status="failed",
        message=(
            "Production-like environments must keep TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none unless the unsafe "
            "override is explicitly enabled."
        ),
    )


def _has_real_value(value: object | None) -> bool:
    """Reject blank and placeholder-like values so dry-run gates cannot pass on templates."""
    normalized = str(value or "").strip()
    if not normalized:
        return False
    upper = normalized.upper()
    if upper.startswith("TBD_") or upper.startswith("REPLACE-WITH-") or upper.startswith("REPLACE_WITH_"):
        return False
    if "<" in normalized and ">" in normalized:
        return False
    return True
