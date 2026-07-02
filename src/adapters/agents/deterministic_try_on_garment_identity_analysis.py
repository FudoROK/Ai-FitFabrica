"""Deterministic Garment Identity analysis for isolated Try-On tests."""

from src.domain.try_on_analysis import TryOnGarmentIdentityAnalysis


class DeterministicTryOnGarmentIdentityAnalysisAdapter:
    """Return a stable test-only garment snapshot."""

    async def analyze(self, *, job_id: str, stored_inputs: list[object]) -> TryOnGarmentIdentityAnalysis:
        return TryOnGarmentIdentityAnalysis(
            invocation_id=f"test-garment-identity-{job_id}",
            prompt_version="garment_identity.test",
            contract_version="garment_identity.contract.test",
            garment_type="test garment",
            dominant_color="test color",
            silhouette_summary="Deterministic test silhouette.",
            confidence=1.0,
            uncertainty_level="low",
        )

