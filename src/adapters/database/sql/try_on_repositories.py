"""SQL-backed Try-On job repository implementation."""

from __future__ import annotations

from sqlalchemy import delete, select

from src.domain.try_on import TryOnJob
from src.use_cases.try_on.ports import TryOnJobRepositoryPort

from .try_on_models import (
    TryOnCostEventRow,
    TryOnErrorRow,
    TryOnHumanIdentityAnalysisRow,
    TryOnGarmentIdentityAnalysisRow,
    TryOnGarmentSlotIdentityAnalysisRow,
    TryOnJobRow,
    TryOnInstructionRow,
    TryOnResultRow,
    TryOnMaterialTextureAnalysisRow,
    TryOnStatusEventRow,
    TryOnStoredInputRow,
)
from .try_on_serialization import job_from_models, job_to_models


class SqlTryOnJobRepository(TryOnJobRepositoryPort):
    """Persist Try-On job aggregates in portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""
        self._session_factory = session_factory

    async def save(self, job: TryOnJob) -> None:
        """Upsert the full Try-On aggregate using focused child tables."""
        serialized = job_to_models(job)
        async with self._session_factory() as session:
            existing = await session.get(TryOnJobRow, job.job_id)
            if existing is None:
                session.add(serialized.job_row)
            else:
                existing.workflow_type = serialized.job_row.workflow_type
                existing.generation_mode = serialized.job_row.generation_mode
                existing.status = serialized.job_row.status
                existing.input_metadata_json = serialized.job_row.input_metadata_json
                existing.wear_control_selections_json = serialized.job_row.wear_control_selections_json
                existing.created_at = serialized.job_row.created_at
                existing.updated_at = serialized.job_row.updated_at

            for row_model in (
                TryOnStoredInputRow,
                TryOnStatusEventRow,
                TryOnCostEventRow,
                TryOnResultRow,
                TryOnErrorRow,
                TryOnHumanIdentityAnalysisRow,
                TryOnGarmentIdentityAnalysisRow,
                TryOnGarmentSlotIdentityAnalysisRow,
                TryOnMaterialTextureAnalysisRow,
                TryOnInstructionRow,
            ):
                await session.execute(delete(row_model).where(row_model.job_id == job.job_id))

            session.add_all(serialized.stored_input_rows)
            session.add_all(serialized.status_event_rows)
            session.add_all(serialized.cost_event_rows)
            if serialized.result_row is not None:
                session.add(serialized.result_row)
            if serialized.error_row is not None:
                session.add(serialized.error_row)
            if serialized.human_identity_analysis_row is not None:
                session.add(serialized.human_identity_analysis_row)
            if serialized.garment_identity_analysis_row is not None:
                session.add(serialized.garment_identity_analysis_row)
            session.add_all(serialized.garment_slot_identity_analysis_rows)
            if serialized.material_texture_analysis_row is not None:
                session.add(serialized.material_texture_analysis_row)
            if serialized.instruction_row is not None:
                session.add(serialized.instruction_row)
            await session.commit()

    async def get(self, job_id: str) -> TryOnJob | None:
        """Load a Try-On aggregate by identifier."""
        async with self._session_factory() as session:
            job_row = await session.get(TryOnJobRow, job_id)
            if job_row is None:
                return None

            stored_input_rows = (
                await session.scalars(select(TryOnStoredInputRow).where(TryOnStoredInputRow.job_id == job_id))
            ).all()
            status_event_rows = (
                await session.scalars(select(TryOnStatusEventRow).where(TryOnStatusEventRow.job_id == job_id))
            ).all()
            cost_event_rows = (
                await session.scalars(select(TryOnCostEventRow).where(TryOnCostEventRow.job_id == job_id))
            ).all()
            result_row = await session.get(TryOnResultRow, job_id)
            error_row = await session.get(TryOnErrorRow, job_id)
            human_identity_analysis_row = await session.get(TryOnHumanIdentityAnalysisRow, job_id)
            garment_identity_analysis_row = await session.get(TryOnGarmentIdentityAnalysisRow, job_id)
            garment_slot_identity_analysis_rows = (
                await session.scalars(
                    select(TryOnGarmentSlotIdentityAnalysisRow).where(
                        TryOnGarmentSlotIdentityAnalysisRow.job_id == job_id
                    )
                )
            ).all()
            material_texture_analysis_row = await session.get(TryOnMaterialTextureAnalysisRow, job_id)
            instruction_row = await session.get(TryOnInstructionRow, job_id)

            return job_from_models(
                job_row=job_row,
                stored_input_rows=list(stored_input_rows),
                status_event_rows=list(status_event_rows),
                cost_event_rows=list(cost_event_rows),
                result_row=result_row,
                error_row=error_row,
                human_identity_analysis_row=human_identity_analysis_row,
                garment_identity_analysis_row=garment_identity_analysis_row,
                garment_slot_identity_analysis_rows=list(garment_slot_identity_analysis_rows),
                material_texture_analysis_row=material_texture_analysis_row,
                instruction_row=instruction_row,
            )

    async def list_recent(self, *, limit: int) -> list[TryOnJob]:
        """Return the most recently updated Try-On aggregates."""
        async with self._session_factory() as session:
            job_rows = (
                await session.scalars(
                    select(TryOnJobRow).order_by(TryOnJobRow.updated_at.desc()).limit(limit)
                )
            ).all()

            jobs: list[TryOnJob] = []
            for job_row in job_rows:
                job_id = job_row.job_id
                stored_input_rows = (
                    await session.scalars(select(TryOnStoredInputRow).where(TryOnStoredInputRow.job_id == job_id))
                ).all()
                status_event_rows = (
                    await session.scalars(select(TryOnStatusEventRow).where(TryOnStatusEventRow.job_id == job_id))
                ).all()
                cost_event_rows = (
                    await session.scalars(select(TryOnCostEventRow).where(TryOnCostEventRow.job_id == job_id))
                ).all()
                result_row = await session.get(TryOnResultRow, job_id)
                error_row = await session.get(TryOnErrorRow, job_id)
                human_identity_analysis_row = await session.get(TryOnHumanIdentityAnalysisRow, job_id)
                garment_identity_analysis_row = await session.get(TryOnGarmentIdentityAnalysisRow, job_id)
                garment_slot_identity_analysis_rows = (
                    await session.scalars(
                        select(TryOnGarmentSlotIdentityAnalysisRow).where(
                            TryOnGarmentSlotIdentityAnalysisRow.job_id == job_id
                        )
                    )
                ).all()
                material_texture_analysis_row = await session.get(TryOnMaterialTextureAnalysisRow, job_id)
                instruction_row = await session.get(TryOnInstructionRow, job_id)
                jobs.append(
                    job_from_models(
                        job_row=job_row,
                        stored_input_rows=list(stored_input_rows),
                        status_event_rows=list(status_event_rows),
                        cost_event_rows=list(cost_event_rows),
                        result_row=result_row,
                        error_row=error_row,
                        human_identity_analysis_row=human_identity_analysis_row,
                        garment_identity_analysis_row=garment_identity_analysis_row,
                        garment_slot_identity_analysis_rows=list(garment_slot_identity_analysis_rows),
                        material_texture_analysis_row=material_texture_analysis_row,
                        instruction_row=instruction_row,
                    )
                )
            return jobs
