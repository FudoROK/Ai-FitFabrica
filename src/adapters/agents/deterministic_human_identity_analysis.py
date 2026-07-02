"""Deterministic Human Identity analysis used only by isolated test runtimes."""

from src.domain.try_on import (
    TryOnHumanIdentityAnalysis,
    TryOnHumanIdentityPreservationTarget,
    TryOnHumanIdentityVerdict,
)


class DeterministicHumanIdentityAnalysisAdapter:
    """Return an approved deterministic snapshot without external provider access."""

    async def analyze(self, *, job_id: str, stored_inputs: list[object]) -> TryOnHumanIdentityAnalysis:
        """Return a stable test-only preservation analysis."""

        return TryOnHumanIdentityAnalysis(
            invocation_id=f"test-human-identity-{job_id}",
            prompt_version="human_identity.test",
            contract_version="human_identity.contract.test",
            face_visibility="fully_visible",
            pose_summary="Deterministic test pose.",
            body_region_visibility=["face", "torso", "arms", "legs"],
            subject_count=1,
            crop_quality="full_body",
            try_on_body_coverage="sufficient",
            occlusion_risk="low",
            required_regions_missing=[],
            preservation_targets=[
                TryOnHumanIdentityPreservationTarget(
                    attribute_name="face",
                    preservation_reason="Required deterministic test preservation target.",
                )
            ],
            confidence=1.0,
            uncertainty_level="low",
            verdict=TryOnHumanIdentityVerdict.ALLOWED,
        )
