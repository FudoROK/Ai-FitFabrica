"""Deterministic fake Try-On generation adapter for the sandbox."""
from __future__ import annotations

from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStoredInput,
    TryOnWorkflowType,
)
from src.use_cases.try_on.ports import TryOnGenerationPort


class FakeTryOnGenerationAdapter(TryOnGenerationPort):
    """Return a deterministic placeholder result behind the generation port."""

    generation_mode = TryOnGenerationMode.SANDBOX_FAKE

    async def generate(
        self,
        *,
        job_id: str,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
    ) -> TryOnResult:
        """Build the sandbox result without calling real AI generation infrastructure."""
        return TryOnResult(
            job_id=job_id,
            workflow_type=TryOnWorkflowType.TRY_ON,
            result_image=TryOnResultImage(
                kind="sandbox_placeholder",
                url="/images/shared/try-on-sandbox-result.svg",
                alt="Sandbox Try-On result preview",
            ),
            quality_report=TryOnQualityReport(
                verdict="pass",
                confidence=0.91,
                checks=[
                    TryOnQualityCheck(
                        name="face_preservation",
                        status="passed",
                        confidence=0.92,
                        message="Sandbox verifier confirms the face-preservation check shape.",
                    ),
                    TryOnQualityCheck(
                        name="garment_similarity",
                        status="passed",
                        confidence=0.9,
                        message="Sandbox verifier confirms garment-similarity reporting shape.",
                    ),
                    TryOnQualityCheck(
                        name="artifact_scan",
                        status="warning",
                        confidence=0.74,
                        message="Sandbox output is deterministic and not a real image generation.",
                    ),
                ],
                limitations=["Sandbox fake generation does not evaluate the uploaded pixels."],
            ),
            stylist_note=(
                "Sandbox Try-On completed. Real stylist advice will be generated after the production generation "
                "adapter is connected."
            ),
            input_metadata=input_metadata,
        )
