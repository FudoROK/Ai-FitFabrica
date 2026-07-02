"""Deterministic Material / Texture analysis for isolated Try-On tests."""

from src.domain.try_on_analysis import TryOnMaterialTextureAnalysis


class DeterministicTryOnMaterialTextureAnalysisAdapter:
    """Return a stable test-only material snapshot."""

    async def analyze(self, *, job_id: str, stored_inputs: list[object]) -> TryOnMaterialTextureAnalysis:
        return TryOnMaterialTextureAnalysis(
            invocation_id=f"test-material-texture-{job_id}",
            prompt_version="material_texture.test",
            contract_version="material_texture.contract.test",
            evidence_note="Deterministic visible material evidence.",
            confidence=1.0,
            uncertainty_level="low",
        )

