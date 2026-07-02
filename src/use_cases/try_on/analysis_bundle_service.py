"""Parallel mandatory analysis orchestration for Try-On workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from src.domain.try_on import TryOnHumanIdentityAnalysis, TryOnStoredInput
from src.domain.try_on import TryOnUploadRole
from src.domain.try_on_analysis import (
    TryOnGarmentIdentityAnalysis,
    TryOnGarmentSlotIdentityAnalysis,
    TryOnMaterialTextureAnalysis,
)

from .analysis_errors import TryOnAnalysisBundleFailure


@dataclass(frozen=True)
class TryOnAnalysisBundle:
    """Validated required analyses ready for workflow persistence."""

    human_identity: TryOnHumanIdentityAnalysis
    garment_identity: TryOnGarmentIdentityAnalysis
    garment_slot_analyses: list[TryOnGarmentSlotIdentityAnalysis]
    material_texture: TryOnMaterialTextureAnalysis


class TryOnAnalysisBundleService:
    """Run required Try-On analyses concurrently and fail closed."""

    def __init__(self, *, human_identity_analyzer, garment_identity_analyzer, material_texture_analyzer) -> None:
        self._human_identity_analyzer = human_identity_analyzer
        self._garment_identity_analyzer = garment_identity_analyzer
        self._material_texture_analyzer = material_texture_analyzer

    async def analyze(self, *, job_id: str, stored_inputs: list[TryOnStoredInput]) -> TryOnAnalysisBundle:
        """Return all required validated analyses or one safe failure."""
        garment_inputs = _garment_inputs(stored_inputs)
        results = await asyncio.gather(
            self._human_identity_analyzer.analyze(job_id=job_id, stored_inputs=stored_inputs),
            self._analyze_garment_slots(job_id=job_id, garment_inputs=garment_inputs),
            self._material_texture_analyzer.analyze(job_id=job_id, stored_inputs=stored_inputs),
            return_exceptions=True,
        )
        failure = next((result for result in results if isinstance(result, BaseException)), None)
        if failure is not None:
            raise TryOnAnalysisBundleFailure() from failure
        human, garment_slots, material = results
        primary_garment = garment_slots[0].analysis
        return TryOnAnalysisBundle(
            human_identity=human,
            garment_identity=primary_garment,
            garment_slot_analyses=garment_slots,
            material_texture=material,
        )

    async def _analyze_garment_slots(
        self,
        *,
        job_id: str,
        garment_inputs: list[TryOnStoredInput],
    ) -> list[TryOnGarmentSlotIdentityAnalysis]:
        if not garment_inputs:
            raise TryOnAnalysisBundleFailure()
        analyses = await asyncio.gather(
            *[
                self._garment_identity_analyzer.analyze(job_id=job_id, stored_inputs=[stored_input])
                for stored_input in garment_inputs
            ]
        )
        return [
            TryOnGarmentSlotIdentityAnalysis(slot_role=stored_input.role.value, analysis=analysis)
            for stored_input, analysis in zip(garment_inputs, analyses, strict=True)
        ]


def _garment_inputs(stored_inputs: list[TryOnStoredInput]) -> list[TryOnStoredInput]:
    """Return garment inputs in deterministic outfit-analysis order."""
    priority = [
        TryOnUploadRole.GARMENT_PHOTO,
        TryOnUploadRole.FULL_BODY_GARMENT_PHOTO,
        TryOnUploadRole.UPPER_GARMENT_PHOTO,
        TryOnUploadRole.LOWER_GARMENT_PHOTO,
        TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO,
    ]
    return [
        stored_input
        for role in priority
        for stored_input in stored_inputs
        if stored_input.role == role
    ]
