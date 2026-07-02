"""In-memory Similar Search event repository for tests and local fallback."""

from __future__ import annotations

from collections import Counter

from src.domain.similar_search import (
    SimilarSearchClickAnalyticsItem,
    SimilarSearchClickAnalyticsResponse,
    SimilarSearchClickAnalyticsSummary,
    SimilarSearchClickEvent,
)


class InMemorySimilarSearchClickEventRepository:
    """Store click events in process memory."""

    def __init__(self) -> None:
        """Initialize an empty event list."""

        self.events: list[SimilarSearchClickEvent] = []

    async def save_click_event(self, event: SimilarSearchClickEvent) -> SimilarSearchClickEvent:
        """Persist one click event in memory."""

        self.events.append(event)
        return event

    async def get_click_analytics(self, *, limit: int) -> SimilarSearchClickAnalyticsResponse:
        """Return aggregate analytics from in-memory events."""

        redirect_clicks = sum(1 for event in self.events if event.redirect_allowed)
        summary = SimilarSearchClickAnalyticsSummary(
            total_clicks=len(self.events),
            redirect_clicks=redirect_clicks,
            local_only_clicks=len(self.events) - redirect_clicks,
        )
        return SimilarSearchClickAnalyticsResponse(
            summary=summary,
            top_products=_top_items(
                Counter((event.product_id, event.title) for event in self.events),
                limit=limit,
            ),
            top_marketplaces=_top_items(
                Counter((event.marketplace, event.marketplace) for event in self.events),
                limit=limit,
            ),
            top_cities=_top_items(
                Counter((event.user_city or "unknown", event.user_city or "unknown") for event in self.events),
                limit=limit,
            ),
        )


def _top_items(counter: Counter[tuple[str, str]], *, limit: int) -> list[SimilarSearchClickAnalyticsItem]:
    """Convert counted pairs into stable analytics items."""

    return [
        SimilarSearchClickAnalyticsItem(key=key, label=label, click_count=count)
        for (key, label), count in counter.most_common(limit)
    ]
