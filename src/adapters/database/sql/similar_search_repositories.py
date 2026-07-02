"""SQL-backed repositories for Similar Search analytics events."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, case, func, select

from src.domain.marketplace_search import (
    MarketplaceConnectorKind,
    MarketplaceDiscoveryCandidate,
    MarketplaceDiscoveryCandidateStatus,
    MarketplaceSourceType,
)
from src.domain.similar_search import (
    SimilarSearchClickAnalyticsItem,
    SimilarSearchClickAnalyticsResponse,
    SimilarSearchClickAnalyticsSummary,
    SimilarSearchClickEvent,
)

from .similar_search_models import MarketplaceDiscoveryCandidateRow, SimilarSearchClickEventRow


class SqlSimilarSearchClickEventRepository:
    """Persist Similar Search click events in PostgreSQL-compatible SQL."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""

        self._session_factory = session_factory

    async def save_click_event(self, event: SimilarSearchClickEvent) -> SimilarSearchClickEvent:
        """Persist one click event."""

        async with self._session_factory() as session:
            session.add(_click_event_to_row(event))
            await session.commit()
        return event

    async def get_click_analytics(self, *, limit: int) -> SimilarSearchClickAnalyticsResponse:
        """Return aggregate click analytics without exposing individual events."""

        async with self._session_factory() as session:
            total_clicks = int(await session.scalar(select(func.count()).select_from(SimilarSearchClickEventRow)) or 0)
            redirect_clicks = int(
                await session.scalar(
                    select(func.count()).select_from(SimilarSearchClickEventRow).where(SimilarSearchClickEventRow.redirect_allowed.is_(True))
                )
                or 0
            )
            top_products = (
                await session.execute(
                    select(
                        SimilarSearchClickEventRow.product_id,
                        func.max(SimilarSearchClickEventRow.title).label("label"),
                        func.count().label("click_count"),
                    )
                    .group_by(SimilarSearchClickEventRow.product_id)
                    .order_by(func.count().desc(), SimilarSearchClickEventRow.product_id.asc())
                    .limit(limit)
                )
            ).all()
            top_marketplaces = (
                await session.execute(
                    select(
                        SimilarSearchClickEventRow.marketplace,
                        SimilarSearchClickEventRow.marketplace.label("label"),
                        func.count().label("click_count"),
                    )
                    .group_by(SimilarSearchClickEventRow.marketplace)
                    .order_by(func.count().desc(), SimilarSearchClickEventRow.marketplace.asc())
                    .limit(limit)
                )
            ).all()
            city_key = case(
                (SimilarSearchClickEventRow.user_city.is_(None), "unknown"),
                else_=SimilarSearchClickEventRow.user_city,
            )
            top_cities = (
                await session.execute(
                    select(
                        city_key.label("city_key"),
                        city_key.label("label"),
                        func.count().label("click_count"),
                    )
                    .group_by(city_key)
                    .order_by(func.count().desc(), city_key.asc())
                    .limit(limit)
                )
            ).all()

        return SimilarSearchClickAnalyticsResponse(
            summary=SimilarSearchClickAnalyticsSummary(
                total_clicks=total_clicks,
                redirect_clicks=redirect_clicks,
                local_only_clicks=total_clicks - redirect_clicks,
            ),
            top_products=_rows_to_items(top_products),
            top_marketplaces=_rows_to_items(top_marketplaces),
            top_cities=_rows_to_items(top_cities),
        )


class SqlMarketplaceCandidateRepository:
    """Persist marketplace/open-web discovery candidates in SQL."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""

        self._session_factory = session_factory

    async def create_candidate(self, candidate: MarketplaceDiscoveryCandidate) -> MarketplaceDiscoveryCandidate:
        """Persist one candidate, deduplicating by source URL within workspace/business scope."""

        async with self._session_factory() as session:
            existing = await _find_candidate_duplicate(session=session, candidate=candidate)
            if existing is not None:
                return _candidate_from_row(existing)
            session.add(_candidate_to_row(candidate))
            await session.commit()
        return candidate

    async def save_candidates(self, candidates: list[MarketplaceDiscoveryCandidate]) -> list[MarketplaceDiscoveryCandidate]:
        """Persist candidates and return durable records after duplicate protection."""

        saved: list[MarketplaceDiscoveryCandidate] = []
        for candidate in candidates:
            saved.append(await self.create_candidate(candidate))
        return saved

    async def get_candidate(self, candidate_id: str) -> MarketplaceDiscoveryCandidate | None:
        """Return one candidate by id."""

        async with self._session_factory() as session:
            row = await session.get(MarketplaceDiscoveryCandidateRow, candidate_id)
            return _candidate_from_row(row) if row is not None else None

    async def list_candidates(
        self,
        *,
        status: MarketplaceDiscoveryCandidateStatus | None = None,
        source_type: MarketplaceSourceType | None = None,
        category: str | None = None,
        city: str | None = None,
        workspace_id: str | None = None,
        business_id: str | None = None,
        limit: int = 20,
    ) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates with optional admin review filters."""

        conditions = []
        if status is not None:
            conditions.append(MarketplaceDiscoveryCandidateRow.status == status.value)
        if source_type is not None:
            conditions.append(MarketplaceDiscoveryCandidateRow.source_type == source_type.value)
        if category is not None:
            conditions.append(MarketplaceDiscoveryCandidateRow.category == category)
        if city is not None:
            conditions.append(MarketplaceDiscoveryCandidateRow.city == city)
        if workspace_id is not None:
            conditions.append(MarketplaceDiscoveryCandidateRow.workspace_id == workspace_id)
        if business_id is not None:
            conditions.append(MarketplaceDiscoveryCandidateRow.business_id == business_id)

        statement = select(MarketplaceDiscoveryCandidateRow).order_by(MarketplaceDiscoveryCandidateRow.created_at.asc()).limit(limit)
        if conditions:
            statement = statement.where(and_(*conditions))

        async with self._session_factory() as session:
            rows = (await session.execute(statement)).scalars()
            return [_candidate_from_row(row) for row in rows]

    async def list_pending_candidates(self, *, limit: int) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates still waiting for admin review."""

        pending = await self.list_candidates(status=MarketplaceDiscoveryCandidateStatus.PENDING, limit=limit)
        if len(pending) >= limit:
            return pending
        legacy_pending = await self.list_candidates(
            status=MarketplaceDiscoveryCandidateStatus.NEEDS_REVIEW,
            limit=limit - len(pending),
        )
        return [*pending, *legacy_pending]

    async def update_candidate_status(
        self,
        *,
        candidate_id: str,
        status: MarketplaceDiscoveryCandidateStatus,
        admin_actor_id: str,
        rejection_reason: str | None = None,
    ) -> MarketplaceDiscoveryCandidate:
        """Persist one admin review decision."""

        async with self._session_factory() as session:
            row = await session.get(MarketplaceDiscoveryCandidateRow, candidate_id)
            if row is None:
                raise KeyError(candidate_id)
            now = datetime.now(UTC)
            row.status = status.value
            row.reviewed_by = admin_actor_id
            row.updated_at = now
            if status is MarketplaceDiscoveryCandidateStatus.APPROVED:
                row.approved_at = now
                row.rejection_reason = None
            if status is MarketplaceDiscoveryCandidateStatus.REJECTED:
                row.rejected_at = now
                row.rejection_reason = rejection_reason
            await session.commit()
            await session.refresh(row)
            return _candidate_from_row(row)


def _click_event_to_row(event: SimilarSearchClickEvent) -> SimilarSearchClickEventRow:
    """Map a domain event into a SQL row."""

    return SimilarSearchClickEventRow(
        event_id=event.event_id,
        product_id=event.product_id,
        title=event.title,
        marketplace=event.marketplace,
        offer_url=event.offer_url,
        image_url=event.image_url,
        user_country_code=event.user_country_code,
        user_city=event.user_city,
        source=event.source,
        redirect_allowed=event.redirect_allowed,
        created_at=event.created_at,
    )


def _rows_to_items(rows: list[object]) -> list[SimilarSearchClickAnalyticsItem]:
    """Map SQL aggregate rows into typed analytics items."""

    return [
        SimilarSearchClickAnalyticsItem(key=str(row[0]), label=str(row[1]), click_count=int(row[2]))
        for row in rows
    ]


def _candidate_to_row(candidate: MarketplaceDiscoveryCandidate) -> MarketplaceDiscoveryCandidateRow:
    """Map a discovery candidate into a SQL row."""

    return MarketplaceDiscoveryCandidateRow(
        candidate_id=candidate.candidate_id,
        workspace_id=candidate.workspace_id,
        business_id=candidate.business_id,
        connector_kind=candidate.connector_kind.value,
        source_type=candidate.source_type.value,
        source_url=str(candidate.source_url),
        image_url=str(candidate.image_url) if candidate.image_url is not None else None,
        media_url=str(candidate.media_url) if candidate.media_url is not None else None,
        source_title=candidate.source_title,
        title=candidate.title,
        name=candidate.name,
        brand=candidate.brand,
        source_snippet=candidate.source_snippet,
        platform_hint=candidate.platform_hint,
        category=candidate.category,
        country_code=candidate.country_code,
        city=candidate.city,
        price_amount=candidate.price_amount,
        currency=candidate.currency,
        raw_payload_json=dict(candidate.raw_payload),
        metadata_json=dict(candidate.metadata),
        status=candidate.status.value,
        reviewed_by=None,
        rejection_reason=candidate.rejection_reason,
        approved_at=candidate.approved_at,
        rejected_at=candidate.rejected_at,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


def _copy_candidate_row(*, source: MarketplaceDiscoveryCandidateRow, target: MarketplaceDiscoveryCandidateRow) -> None:
    """Copy mutable candidate fields into an existing row."""

    target.connector_kind = source.connector_kind
    target.source_type = source.source_type
    target.source_url = source.source_url
    target.source_title = source.source_title
    target.source_snippet = source.source_snippet
    target.platform_hint = source.platform_hint
    target.category = source.category
    target.country_code = source.country_code
    target.city = source.city
    target.status = source.status
    target.updated_at = source.updated_at


def _candidate_from_row(row: MarketplaceDiscoveryCandidateRow) -> MarketplaceDiscoveryCandidate:
    """Map one SQL row into the domain contract."""

    return MarketplaceDiscoveryCandidate(
        candidate_id=row.candidate_id,
        workspace_id=row.workspace_id,
        business_id=row.business_id,
        connector_kind=MarketplaceConnectorKind(row.connector_kind),
        source_type=MarketplaceSourceType(row.source_type),
        source_url=row.source_url,
        image_url=row.image_url,
        media_url=row.media_url,
        source_title=row.source_title,
        title=row.title,
        name=row.name,
        brand=row.brand,
        source_snippet=row.source_snippet,
        platform_hint=row.platform_hint,
        category=row.category,
        country_code=row.country_code,
        city=row.city,
        price_amount=row.price_amount,
        currency=row.currency,
        raw_payload=dict(row.raw_payload_json or {}),
        metadata=dict(row.metadata_json or {}),
        status=MarketplaceDiscoveryCandidateStatus(row.status),
        rejection_reason=row.rejection_reason,
        approved_at=row.approved_at,
        rejected_at=row.rejected_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _find_candidate_duplicate(*, session, candidate: MarketplaceDiscoveryCandidate) -> MarketplaceDiscoveryCandidateRow | None:
    """Return an existing candidate in the same scope with the same source URL."""

    statement = select(MarketplaceDiscoveryCandidateRow).where(
        MarketplaceDiscoveryCandidateRow.source_url == str(candidate.source_url),
        MarketplaceDiscoveryCandidateRow.workspace_id.is_(None)
        if candidate.workspace_id is None
        else MarketplaceDiscoveryCandidateRow.workspace_id == candidate.workspace_id,
        MarketplaceDiscoveryCandidateRow.business_id.is_(None)
        if candidate.business_id is None
        else MarketplaceDiscoveryCandidateRow.business_id == candidate.business_id,
    )
    return (await session.execute(statement)).scalars().first()
