"""Deterministic Garment Identity analysis used only by test runtimes."""

from src.domain.product_card import ProductCardGarmentAnalysis


class DeterministicGarmentIdentityAnalysisAdapter:
    """Return a stable validated garment snapshot without provider access."""

    async def analyze(self, *, job_id: str, asset_keys: list[str]) -> ProductCardGarmentAnalysis:
        """Return deterministic garment facts for isolated tests."""
        return ProductCardGarmentAnalysis(
            job_id=job_id,
            invocation_id=f"test-garment-identity-{job_id}",
            prompt_version="garment_identity.test",
            contract_version="garment_identity.contract.test",
            garment_type="test garment",
            dominant_color="test color",
            silhouette_summary="Deterministic test silhouette.",
            preserved_details=["deterministic detail"],
            confidence=1.0,
            uncertainty_level="low",
        )
