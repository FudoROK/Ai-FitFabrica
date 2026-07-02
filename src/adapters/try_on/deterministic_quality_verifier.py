"""Deterministic backend-owned Try-On quality verification adapter."""

from __future__ import annotations

from src.adapters.storage.contracts import ObjectStorage
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnStoredInput,
)
from src.use_cases.try_on.ports import TryOnQualityVerifierPort
from src.use_cases.try_on.quality_policy import TryOnQualityPolicy


class DeterministicTryOnQualityVerifier(TryOnQualityVerifierPort):
    """Perform deterministic backend-side checks before exposing Try-On results."""

    def __init__(self, *, object_storage: ObjectStorage, minimum_generated_bytes: int = 64) -> None:
        """Store the object-storage dependency and minimum artifact sanity threshold."""
        self._object_storage = object_storage
        self._minimum_generated_bytes = minimum_generated_bytes
        self._quality_policy = TryOnQualityPolicy(minimum_pass_confidence=0.8)

    async def verify(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> TryOnQualityReport:
        """Return a deterministic quality report for the generated Try-On result."""
        if result.result_image.kind == "sandbox_placeholder":
            return result.quality_report

        artifact_object_key = result.result_image._artifact_object_key
        checks: list[TryOnQualityCheck] = [
            TryOnQualityCheck(
                name="workflow_input_shape",
                status="passed" if len(input_metadata) >= 2 and len(stored_inputs) >= 2 else "failed",
                confidence=0.84 if len(input_metadata) >= 2 and len(stored_inputs) >= 2 else 0.22,
                message=(
                    "Try-On workflow retained both user inputs through generation."
                    if len(input_metadata) >= 2 and len(stored_inputs) >= 2
                    else "Try-On workflow lost required input references before quality verification."
                ),
            ),
            TryOnQualityCheck(
                name="generated_artifact_reference",
                status="passed" if artifact_object_key else "failed",
                confidence=0.9 if artifact_object_key else 0.14,
                message=(
                    "Generated result retains an internal backend artifact reference for verification."
                    if artifact_object_key
                    else "Generated result is missing an internal backend artifact reference."
                ),
            ),
        ]

        garment_slot_roles = _garment_slot_roles(input_metadata)
        stored_garment_slot_roles = _garment_slot_roles(stored_inputs)
        if len(garment_slot_roles) > 1:
            slots_match = garment_slot_roles == stored_garment_slot_roles
            checks.append(
                TryOnQualityCheck(
                    name="outfit_slot_input_shape",
                    status="passed" if slots_match else "failed",
                    confidence=0.86 if slots_match else 0.22,
                    message=(
                        f"Quality verifier retained outfit garment slots: {', '.join(garment_slot_roles)}."
                        if slots_match
                        else "Quality verifier detected mismatch between request garment slots and stored inputs."
                    ),
                )
            )

        artifact_bytes = b""
        if artifact_object_key:
            artifact_bytes = self._object_storage.get_bytes(artifact_object_key)
        checks.append(
            TryOnQualityCheck(
                name="generated_artifact_non_empty",
                status="passed" if artifact_bytes else "failed",
                confidence=0.88 if artifact_bytes else 0.1,
                message=(
                    "Generated artifact bytes were loaded successfully from backend storage."
                    if artifact_bytes
                    else "Generated artifact bytes could not be loaded from backend storage."
                ),
            )
        )
        checks.append(
            TryOnQualityCheck(
                name="generated_artifact_size_sanity",
                status="passed" if len(artifact_bytes) >= self._minimum_generated_bytes else "warning",
                confidence=0.82 if len(artifact_bytes) >= self._minimum_generated_bytes else 0.58,
                message=(
                    "Generated artifact size passed the deterministic backend sanity threshold."
                    if len(artifact_bytes) >= self._minimum_generated_bytes
                    else "Generated artifact is very small; a dedicated visual verifier should inspect fidelity."
                ),
            )
        )
        checks.append(
            TryOnQualityCheck(
                name="generation_backend_trace",
                status="passed",
                confidence=0.8,
                message=f"Quality verifier recorded backend generation mode {generation_mode.value}.",
            )
        )

        failed_checks = [check for check in checks if check.status == "failed"]
        if failed_checks:
            return self._quality_policy.evaluate(
                TryOnQualityReport(
                    verdict="reject",
                    confidence=0.24,
                    checks=checks,
                    limitations=[
                        "Result was rejected by backend deterministic verification before user exposure."
                    ],
                )
            )

        warning_checks = [check for check in checks if check.status == "warning"]
        if warning_checks:
            return self._quality_policy.evaluate(
                TryOnQualityReport(
                    verdict="repair_recommended",
                    confidence=0.61,
                    checks=checks,
                    limitations=[
                        "A local backend repair pass is recommended before the result is exposed to the user."
                    ],
                )
            )

        limitations = [
            "Dedicated visual identity, garment-detail, and artifact quality verification still needs a stricter model-backed verifier."
        ]
        if generation_mode == TryOnGenerationMode.PROVIDER_RUNTIME:
            limitations.append(
                "Provider-runtime image editing still persists deterministic placeholder-like artifacts until the dedicated image-byte path is fully upgraded."
            )

        return self._quality_policy.evaluate(
            TryOnQualityReport(
                verdict="pass",
                confidence=0.86 if generation_mode == TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON else 0.74,
                checks=checks,
                limitations=limitations,
            )
        )


def _garment_slot_roles(items: list[TryOnInputMetadata] | list[TryOnStoredInput]) -> list[str]:
    """Return garment slot roles in request/storage order, excluding the human input."""
    return [item.role.value for item in items if item.role.value != "human_photo"]
