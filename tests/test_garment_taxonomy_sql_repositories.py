from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import pytest

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.garment_taxonomy_repositories import SqlGarmentTaxonomyRepository
from src.domain.garment_taxonomy import (
    GarmentTaxonomyCandidate,
    GarmentTaxonomyCandidateStatus,
    GarmentTaxonomyItem,
    GarmentWearControl,
)


@pytest.mark.asyncio
async def test_sql_garment_taxonomy_repository_round_trips_catalog_and_candidate() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlGarmentTaxonomyRepository(session_factory=session_factory)

    await repository.upsert_item(
        GarmentTaxonomyItem(
            code="shirt",
            category="tops",
            display_name="Shirt",
        )
    )
    await repository.upsert_control(
        GarmentWearControl(
            taxonomy_item_code="shirt",
            control_code="untucked",
            display_name="Навыпуск",
            instruction_template="Keep the shirt hem visible over the waistband.",
            default_for_auto=True,
        )
    )
    await repository.upsert_control(
        GarmentWearControl(
            parent_category_code="tops",
            control_code="relaxed_fit",
            display_name="Свободнее",
            instruction_template="Keep the top relaxed.",
        )
    )

    item = await repository.get_item_by_code("shirt")
    controls = await repository.list_controls_for_item_or_parent("shirt")
    candidate = await repository.save_candidate(
        GarmentTaxonomyCandidate(
            proposed_code="kimono jacket",
            proposed_display_name="Kimono jacket",
            proposed_category="outerwear",
            proposed_controls=["open", "draped"],
            source_job_ids=["try_on_123"],
            confidence=0.74,
            agent_reasoning_summary="Open lightweight outerwear layer.",
        )
    )

    assert item is not None
    assert item.code == "shirt"
    assert [control.control_code for control in controls] == ["untucked", "relaxed_fit"]
    assert controls[0].default_for_auto is True
    assert candidate.status == GarmentTaxonomyCandidateStatus.PENDING_REVIEW
    assert candidate.proposed_code == "kimono_jacket"
    assert await repository.get_item_by_code("kimono_jacket") is None

    await engine.dispose()
