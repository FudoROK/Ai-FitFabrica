"""Reusable approved Human Identity analysis stub for non-agent Try-On tests."""

from src.domain.try_on import (
    TryOnHumanIdentityAnalysis,
    TryOnHumanIdentityPreservationTarget,
    TryOnHumanIdentityVerdict,
)


class AllowingHumanIdentityAnalysisStub:
    """Return one deterministic policy-approved analysis snapshot."""

    async def analyze(self, **_kwargs) -> TryOnHumanIdentityAnalysis:
        """Return an approved human-preservation analysis."""

        return TryOnHumanIdentityAnalysis(
            invocation_id="test-human-identity-invocation",
            prompt_version="human_identity.test",
            contract_version="human_identity.contract.test",
            face_visibility="fully_visible",
            pose_summary="Test-approved front-facing pose.",
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
