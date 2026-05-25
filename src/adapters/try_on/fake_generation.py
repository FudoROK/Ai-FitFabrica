"""Deterministic fake Try-On generation adapter for the sandbox."""
from __future__ import annotations

from src.domain.try_on import (
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnWorkflowType,
)
from src.use_cases.try_on.ports import TryOnGenerationPort


class FakeTryOnGenerationAdapter(TryOnGenerationPort):
    """Return a deterministic placeholder result behind the generation port."""

    async def generate(self, job_id: str, input_metadata: list[TryOnInputMetadata]) -> TryOnResult:
        """Build the sandbox result without calling real AI generation infrastructure."""
        return TryOnResult(
            job_id=job_id,
            workflow_type=TryOnWorkflowType.TRY_ON,
            result_image=TryOnResultImage(
                kind="sandbox_placeholder",
                url="/images/shared/try-on-sandbox-result.webp",
                alt="Sandbox Try-On result preview",
            ),
            quality_report=TryOnQualityReport(
                verdict="pass",
                confidence=0.91,
                checks=[
                    TryOnQualityCheck(
                        name="face_preservation",
                        status="passed",
                        confidence=0.93,
                        message="Sandbox placeholder preserves the submitted human identity contract.",
                    ),
                    TryOnQualityCheck(
                        name="garment_similarity",
                        status="passed",
                        confidence=0.9,
                        message="Sandbox placeholder keeps garment matching behind the backend contract.",
                    ),
                    TryOnQualityCheck(
                        name="artifact_scan",
                        status="passed",
                        confidence=0.89,
                        message="No blocking sandbox artifacts were detected.",
                    ),
                ],
                limitations=["This sandbox result is deterministic and does not perform real AI generation."],
            ),
            stylist_note=(
                "Sandbox Try-On completed. The backend accepted both images, ran the placeholder generation "
                "port, and verified the result before exposing it."
            ),
            input_metadata=input_metadata,
        )
