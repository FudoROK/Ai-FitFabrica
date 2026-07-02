from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.database.sql.try_on_models import (
    TryOnGarmentIdentityAnalysisRow,
    TryOnGarmentSlotIdentityAnalysisRow,
    TryOnMaterialTextureAnalysisRow,
)
from src.adapters.database.sql.try_on_serialization import job_from_models, job_to_models
from src.domain.try_on import TryOnGenerationMode, TryOnJob, TryOnJobStatus
from src.domain.try_on_analysis import (
    TryOnGarmentIdentityAnalysis,
    TryOnGarmentSlotIdentityAnalysis,
    TryOnMaterialTextureAnalysis,
)


def _job() -> TryOnJob:
    now = datetime.now(timezone.utc)
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
    return TryOnJob(
        job_id="try-on-analysis-1",
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        status=TryOnJobStatus.ACCEPTED,
        created_at=now,
        updated_at=now,
        garment_identity_analysis=garment_identity,
        garment_slot_analyses=[
            TryOnGarmentSlotIdentityAnalysis(slot_role="outerwear_garment_photo", analysis=garment_identity)
        ],
        material_texture_analysis=TryOnMaterialTextureAnalysis(
            invocation_id="material-1",
            prompt_version="material.v1",
            contract_version="material.contract.v1",
            evidence_note="Matte woven surface.",
            confidence=0.9,
            uncertainty_level="medium",
        ),
    )


def test_try_on_analysis_bundle_sql_rows_are_separate_child_entities() -> None:
    assert TryOnGarmentIdentityAnalysisRow.__tablename__ == "try_on_garment_identity_analyses"
    assert TryOnGarmentSlotIdentityAnalysisRow.__tablename__ == "try_on_garment_slot_identity_analyses"
    assert TryOnMaterialTextureAnalysisRow.__tablename__ == "try_on_material_texture_analyses"


def test_try_on_analysis_bundle_serialization_round_trip() -> None:
    serialized = job_to_models(_job())

    restored = job_from_models(
        job_row=serialized.job_row,
        stored_input_rows=[],
        status_event_rows=[],
        cost_event_rows=[],
        result_row=None,
        error_row=None,
        human_identity_analysis_row=None,
        garment_identity_analysis_row=serialized.garment_identity_analysis_row,
        garment_slot_identity_analysis_rows=serialized.garment_slot_identity_analysis_rows,
        material_texture_analysis_row=serialized.material_texture_analysis_row,
    )

    assert restored.garment_identity_analysis is not None
    assert restored.garment_identity_analysis.garment_type == "coat"
    assert [item.slot_role for item in restored.garment_slot_analyses] == ["outerwear_garment_photo"]
    assert restored.garment_slot_analyses[0].analysis.garment_type == "coat"
    assert restored.material_texture_analysis is not None
    assert restored.material_texture_analysis.evidence_note == "Matte woven surface."
