from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.similar_search_repositories import SqlMarketplaceCandidateRepository
from src.domain.marketplace_search import (
    MarketplaceConnectorKind,
    MarketplaceDiscoveryCandidate,
    MarketplaceDiscoveryCandidateStatus,
    MarketplaceSourceType,
)
from src.use_cases.similar_search.candidate_review import (
    InMemoryMarketplaceCandidateRepository,
    MarketplaceCandidateReviewService,
)


def _candidate(
    candidate_id: str = "candidate-1",
    *,
    source_url: str | None = None,
    category: str = "shirt",
    city: str = "Almaty",
    workspace_id: str | None = "workspace-1",
    business_id: str | None = "business-1",
) -> MarketplaceDiscoveryCandidate:
    return MarketplaceDiscoveryCandidate(
        candidate_id=candidate_id,
        workspace_id=workspace_id,
        business_id=business_id,
        connector_kind=MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
        source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
        source_url=source_url or f"https://www.instagram.com/example_shop/p/{candidate_id}",
        source_title="Example shop white shirt",
        source_snippet="White shirt in Almaty.",
        platform_hint="instagram",
        image_url="https://cdn.example.test/shirt.jpg",
        title="Example shop white shirt",
        brand="Example Shop",
        category=category,
        country_code="KZ",
        city=city,
        price_amount=12000.0,
        currency="KZT",
        raw_payload={"provider": "search_api", "rank": 1},
        metadata={"query": "site:instagram.com shirt Almaty"},
    )


@pytest.mark.asyncio
async def test_candidate_review_service_saves_and_lists_pending_candidates() -> None:
    service = MarketplaceCandidateReviewService(repository=InMemoryMarketplaceCandidateRepository())

    saved = await service.save_candidates(candidates=[_candidate()])
    pending = await service.list_pending_candidates(limit=10)

    assert [candidate.candidate_id for candidate in saved] == ["candidate-1"]
    assert [candidate.candidate_id for candidate in pending] == ["candidate-1"]
    assert pending[0].status is MarketplaceDiscoveryCandidateStatus.PENDING


@pytest.mark.asyncio
async def test_candidate_review_service_approves_and_rejects_candidates() -> None:
    service = MarketplaceCandidateReviewService(repository=InMemoryMarketplaceCandidateRepository())
    await service.save_candidates(candidates=[_candidate("approved-1"), _candidate("rejected-1")])

    approved = await service.approve_candidate(candidate_id="approved-1", admin_actor_id="admin-1")
    rejected = await service.reject_candidate(candidate_id="rejected-1", admin_actor_id="admin-1")
    pending = await service.list_pending_candidates(limit=10)

    assert approved.status is MarketplaceDiscoveryCandidateStatus.APPROVED
    assert rejected.status is MarketplaceDiscoveryCandidateStatus.REJECTED
    assert pending == []


@pytest.mark.asyncio
async def test_sql_candidate_repository_round_trips_admin_review_decisions() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlMarketplaceCandidateRepository(session_factory=session_factory)

    await repository.save_candidates([_candidate("candidate-sql-1"), _candidate("candidate-sql-2")])
    approved = await repository.update_candidate_status(
        candidate_id="candidate-sql-1",
        status=MarketplaceDiscoveryCandidateStatus.APPROVED,
        admin_actor_id="admin-1",
    )
    pending = await repository.list_pending_candidates(limit=10)

    assert approved.status is MarketplaceDiscoveryCandidateStatus.APPROVED
    assert [candidate.candidate_id for candidate in pending] == ["candidate-sql-2"]

    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_candidate_repository_prevents_duplicates_by_source_url_and_scope() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlMarketplaceCandidateRepository(session_factory=session_factory)

    await repository.create_candidate(_candidate("candidate-original"))
    saved = await repository.create_candidate(
        _candidate("candidate-duplicate", source_url="https://www.instagram.com/example_shop/p/candidate-original")
    )
    other_scope = await repository.create_candidate(
        _candidate(
            "candidate-other-scope",
            source_url="https://www.instagram.com/example_shop/p/candidate-original",
            workspace_id="workspace-2",
            business_id="business-1",
        )
    )
    candidates = await repository.list_candidates(limit=10)

    assert saved.candidate_id == "candidate-original"
    assert other_scope.candidate_id == "candidate-other-scope"
    assert [candidate.candidate_id for candidate in candidates] == ["candidate-original", "candidate-other-scope"]

    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_candidate_repository_lists_candidates_with_filters() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlMarketplaceCandidateRepository(session_factory=session_factory)

    await repository.save_candidates(
        [
            _candidate("candidate-almaty-shirt", category="shirt", city="Almaty"),
            _candidate(
                "candidate-astana-dress",
                source_url="https://example.test/dress",
                category="dress",
                city="Astana",
            ),
        ]
    )
    await repository.update_candidate_status(
        candidate_id="candidate-astana-dress",
        status=MarketplaceDiscoveryCandidateStatus.REJECTED,
        admin_actor_id="admin-1",
        rejection_reason="not a product page",
    )

    filtered = await repository.list_candidates(
        status=MarketplaceDiscoveryCandidateStatus.PENDING,
        source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
        category="shirt",
        city="Almaty",
        limit=10,
    )

    assert [candidate.candidate_id for candidate in filtered] == ["candidate-almaty-shirt"]

    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_candidate_repository_get_reject_archive_and_persists_after_reinit() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlMarketplaceCandidateRepository(session_factory=session_factory)

    await repository.create_candidate(_candidate("candidate-review"))
    rejected = await repository.update_candidate_status(
        candidate_id="candidate-review",
        status=MarketplaceDiscoveryCandidateStatus.REJECTED,
        admin_actor_id="admin-1",
        rejection_reason="duplicate account",
    )
    archived = await repository.update_candidate_status(
        candidate_id="candidate-review",
        status=MarketplaceDiscoveryCandidateStatus.ARCHIVED,
        admin_actor_id="admin-1",
    )

    reinitialized = SqlMarketplaceCandidateRepository(session_factory=session_factory)
    loaded = await reinitialized.get_candidate("candidate-review")

    assert rejected.rejection_reason == "duplicate account"
    assert rejected.rejected_at is not None
    assert archived.status is MarketplaceDiscoveryCandidateStatus.ARCHIVED
    assert loaded is not None
    assert loaded.candidate_id == "candidate-review"
    assert loaded.status is MarketplaceDiscoveryCandidateStatus.ARCHIVED
    assert loaded.raw_payload == {"provider": "search_api", "rank": 1}

    await engine.dispose()
