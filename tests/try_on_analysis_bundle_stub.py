"""Test-only helpers for constructing the mandatory Try-On analysis bundle."""

from src.adapters.agents.deterministic_try_on_garment_identity_analysis import (
    DeterministicTryOnGarmentIdentityAnalysisAdapter,
)
from src.adapters.agents.deterministic_try_on_material_texture_analysis import (
    DeterministicTryOnMaterialTextureAnalysisAdapter,
)
from src.domain.try_on import TryOnHumanIdentityAnalysis, TryOnHumanIdentityVerdict
from src.domain.try_on_analysis import (
    TryOnGarmentIdentityAnalysis,
    TryOnGarmentSlotIdentityAnalysis,
    TryOnMaterialTextureAnalysis,
)
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundle, TryOnAnalysisBundleService


def required_analysis_bundle(human_identity_analyzer) -> TryOnAnalysisBundleService:
    """Return a test bundle with the supplied Human Identity analyzer."""
    return TryOnAnalysisBundleService(
        human_identity_analyzer=human_identity_analyzer,
        garment_identity_analyzer=DeterministicTryOnGarmentIdentityAnalysisAdapter(),
        material_texture_analyzer=DeterministicTryOnMaterialTextureAnalysisAdapter(),
    )


def approved_analysis_bundle() -> TryOnAnalysisBundle:
    """Return a fully approved structured bundle without storage references."""
    garment_identity = TryOnGarmentIdentityAnalysis(
        invocation_id="garment-1",
        prompt_version="garment.v1",
        contract_version="garment.contract.v1",
        garment_type="coat",
        dominant_color="brown",
        silhouette_summary="Straight coat.",
        confidence=0.94,
        uncertainty_level="low",
    )
    return TryOnAnalysisBundle(
        human_identity=TryOnHumanIdentityAnalysis(
            invocation_id="human-1",
            prompt_version="human.v1",
            contract_version="human.contract.v1",
            face_visibility="fully_visible",
            pose_summary="Front pose.",
            body_region_visibility=["face", "torso", "arms", "legs"],
            subject_count=1,
            crop_quality="full_body",
            try_on_body_coverage="sufficient",
            occlusion_risk="low",
            required_regions_missing=[],
            confidence=0.95,
            uncertainty_level="low",
            verdict=TryOnHumanIdentityVerdict.ALLOWED,
        ),
        garment_identity=garment_identity,
        garment_slot_analyses=[
            TryOnGarmentSlotIdentityAnalysis(slot_role="garment_photo", analysis=garment_identity)
        ],
        material_texture=TryOnMaterialTextureAnalysis(
            invocation_id="material-1",
            prompt_version="material.v1",
            contract_version="material.contract.v1",
            evidence_note="Visible matte woven surface.",
            confidence=0.9,
            uncertainty_level="medium",
        ),
    )
