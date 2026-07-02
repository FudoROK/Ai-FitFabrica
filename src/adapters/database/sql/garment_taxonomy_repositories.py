"""SQL-backed garment taxonomy repository."""

from __future__ import annotations

from sqlalchemy import select

from src.domain.garment_taxonomy import (
    GarmentTaxonomyAuditEvent,
    GarmentTaxonomyCandidate,
    GarmentTaxonomyCandidateStatus,
    GarmentTaxonomyItem,
    GarmentWearControl,
    GarmentWearControlRiskLevel,
)

from .garment_taxonomy_models import (
    GarmentTaxonomyAuditLogRow,
    GarmentTaxonomyCandidateRow,
    GarmentTaxonomyItemRow,
    GarmentWearControlRow,
)


class SqlGarmentTaxonomyRepository:
    """Persist and read garment taxonomy catalog data."""

    def __init__(self, *, session_factory) -> None:
        self._session_factory = session_factory

    async def upsert_item(self, item: GarmentTaxonomyItem) -> GarmentTaxonomyItem:
        """Insert or update one approved taxonomy item."""
        async with self._session_factory() as session:
            row = await session.get(GarmentTaxonomyItemRow, item.code)
            if row is None:
                row = GarmentTaxonomyItemRow(
                    code=item.code,
                    parent_code=item.parent_code,
                    category=item.category,
                    display_name=item.display_name,
                    description=item.description,
                    active=item.active,
                    version=item.version,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                session.add(row)
            else:
                row.parent_code = item.parent_code
                row.category = item.category
                row.display_name = item.display_name
                row.description = item.description
                row.active = item.active
                row.version = item.version
                row.updated_at = item.updated_at
            await session.commit()
            return item

    async def upsert_control(self, control: GarmentWearControl) -> GarmentWearControl:
        """Insert or update one approved wear control."""
        async with self._session_factory() as session:
            row = await session.get(GarmentWearControlRow, control.id)
            if row is None:
                row = GarmentWearControlRow(
                    id=control.id,
                    taxonomy_item_code=control.taxonomy_item_code,
                    parent_category_code=control.parent_category_code,
                    control_code=control.control_code,
                    display_name=control.display_name,
                    description=control.description,
                    instruction_template=control.instruction_template,
                    risk_level=control.risk_level.value,
                    default_for_auto=control.default_for_auto,
                    active=control.active,
                    version=control.version,
                )
                session.add(row)
            else:
                row.taxonomy_item_code = control.taxonomy_item_code
                row.parent_category_code = control.parent_category_code
                row.control_code = control.control_code
                row.display_name = control.display_name
                row.description = control.description
                row.instruction_template = control.instruction_template
                row.risk_level = control.risk_level.value
                row.default_for_auto = control.default_for_auto
                row.active = control.active
                row.version = control.version
            await session.commit()
            return control

    async def get_item_by_code(self, code: str) -> GarmentTaxonomyItem | None:
        """Return one approved taxonomy item by normalized code."""
        async with self._session_factory() as session:
            row = await session.get(GarmentTaxonomyItemRow, code)
            return _item_from_row(row) if row is not None else None

    async def list_controls_for_item_or_parent(self, code: str) -> list[GarmentWearControl]:
        """Return active controls scoped to the taxonomy item or its category."""
        async with self._session_factory() as session:
            item_row = await session.get(GarmentTaxonomyItemRow, code)
            if item_row is None:
                return []
            statement = (
                select(GarmentWearControlRow)
                .where(GarmentWearControlRow.active.is_(True))
                .where(
                    (GarmentWearControlRow.taxonomy_item_code == item_row.code)
                    | (GarmentWearControlRow.parent_category_code == item_row.category)
                )
                .order_by(GarmentWearControlRow.taxonomy_item_code.desc(), GarmentWearControlRow.control_code.asc())
            )
            rows = (await session.execute(statement)).scalars().all()
            return [_control_from_row(row) for row in rows]

    async def save_candidate(self, candidate: GarmentTaxonomyCandidate) -> GarmentTaxonomyCandidate:
        """Persist one taxonomy candidate without mutating the production catalog."""
        async with self._session_factory() as session:
            row = GarmentTaxonomyCandidateRow(
                id=candidate.id,
                proposed_code=candidate.proposed_code,
                proposed_display_name=candidate.proposed_display_name,
                proposed_parent_code=candidate.proposed_parent_code,
                proposed_category=candidate.proposed_category,
                proposed_controls_json=list(candidate.proposed_controls),
                source_job_ids_json=list(candidate.source_job_ids),
                examples_count=candidate.examples_count,
                confidence=candidate.confidence,
                agent_reasoning_summary=candidate.agent_reasoning_summary,
                status=candidate.status.value,
                reviewed_by=candidate.reviewed_by,
                reviewed_at=candidate.reviewed_at,
                review_reason=candidate.review_reason,
                approved_catalog_item_code=candidate.approved_catalog_item_code,
                created_at=candidate.created_at,
            )
            session.add(row)
            await session.commit()
            return candidate

    async def list_candidates(
        self,
        status: GarmentTaxonomyCandidateStatus | None = None,
    ) -> list[GarmentTaxonomyCandidate]:
        """Return candidates, optionally filtered by review status."""
        async with self._session_factory() as session:
            statement = select(GarmentTaxonomyCandidateRow).order_by(GarmentTaxonomyCandidateRow.created_at.desc())
            if status is not None:
                statement = statement.where(GarmentTaxonomyCandidateRow.status == status.value)
            rows = (await session.execute(statement)).scalars().all()
            return [_candidate_from_row(row) for row in rows]

    async def get_candidate(self, candidate_id: str) -> GarmentTaxonomyCandidate | None:
        """Return one taxonomy candidate by id."""
        async with self._session_factory() as session:
            row = await session.get(GarmentTaxonomyCandidateRow, candidate_id)
            return _candidate_from_row(row) if row is not None else None

    async def update_candidate(self, candidate: GarmentTaxonomyCandidate) -> GarmentTaxonomyCandidate:
        """Persist one reviewed taxonomy candidate state."""
        async with self._session_factory() as session:
            row = await session.get(GarmentTaxonomyCandidateRow, candidate.id)
            if row is None:
                raise ValueError(f"taxonomy candidate {candidate.id!r} was not found")
            row.proposed_code = candidate.proposed_code
            row.proposed_display_name = candidate.proposed_display_name
            row.proposed_parent_code = candidate.proposed_parent_code
            row.proposed_category = candidate.proposed_category
            row.proposed_controls_json = list(candidate.proposed_controls)
            row.source_job_ids_json = list(candidate.source_job_ids)
            row.examples_count = candidate.examples_count
            row.confidence = candidate.confidence
            row.agent_reasoning_summary = candidate.agent_reasoning_summary
            row.status = candidate.status.value
            row.reviewed_by = candidate.reviewed_by
            row.reviewed_at = candidate.reviewed_at
            row.review_reason = candidate.review_reason
            row.approved_catalog_item_code = candidate.approved_catalog_item_code
            await session.commit()
            return candidate

    async def write_audit_event(self, event: GarmentTaxonomyAuditEvent) -> GarmentTaxonomyAuditEvent:
        """Persist one taxonomy mutation audit event."""
        async with self._session_factory() as session:
            session.add(
                GarmentTaxonomyAuditLogRow(
                    id=event.id,
                    actor_id=event.actor_id,
                    action=event.action.value,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    before_json=dict(event.before_json),
                    after_json=dict(event.after_json),
                    created_at=event.created_at,
                )
            )
            await session.commit()
            return event


def _item_from_row(row: GarmentTaxonomyItemRow) -> GarmentTaxonomyItem:
    return GarmentTaxonomyItem(
        code=row.code,
        parent_code=row.parent_code,
        category=row.category,
        display_name=row.display_name,
        description=row.description,
        active=row.active,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _control_from_row(row: GarmentWearControlRow) -> GarmentWearControl:
    return GarmentWearControl(
        id=row.id,
        taxonomy_item_code=row.taxonomy_item_code,
        parent_category_code=row.parent_category_code,
        control_code=row.control_code,
        display_name=row.display_name,
        description=row.description,
        instruction_template=row.instruction_template,
        risk_level=GarmentWearControlRiskLevel(row.risk_level),
        default_for_auto=row.default_for_auto,
        active=row.active,
        version=row.version,
    )


def _candidate_from_row(row: GarmentTaxonomyCandidateRow) -> GarmentTaxonomyCandidate:
    return GarmentTaxonomyCandidate(
        id=row.id,
        proposed_code=row.proposed_code,
        proposed_display_name=row.proposed_display_name,
        proposed_parent_code=row.proposed_parent_code,
        proposed_category=row.proposed_category,
        proposed_controls=list(row.proposed_controls_json or []),
        source_job_ids=list(row.source_job_ids_json or []),
        examples_count=row.examples_count,
        confidence=row.confidence,
        agent_reasoning_summary=row.agent_reasoning_summary,
        status=GarmentTaxonomyCandidateStatus(row.status),
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        review_reason=row.review_reason,
        approved_catalog_item_code=row.approved_catalog_item_code,
        created_at=row.created_at,
    )
