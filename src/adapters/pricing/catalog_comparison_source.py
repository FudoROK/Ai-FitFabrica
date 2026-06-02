"""Catalog-backed comparable source for pricing workflows."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.pricing import PricingComparable
from src.use_cases.pricing.ports import PricingBrief, PricingComparisonSourcePort


@dataclass(frozen=True)
class CatalogPricingComparisonSource(PricingComparisonSourcePort):
    """Use catalog offer truth as the first comparable source for pricing."""

    catalog_repository: object

    async def list_comparables(self, brief: PricingBrief) -> list[PricingComparable]:
        """Return comparable market evidence for the requested pricing brief."""
        offers = await self.catalog_repository.list_offers_for_products(
            [brief.product_id],
            marketplace_filters=[],
        )
        return [
            PricingComparable(
                source_id=offer.offer_id,
                price_amount=offer.price_amount,
                currency=offer.currency,
            )
            for offer in offers
            if offer.currency == brief.target_currency
        ]
