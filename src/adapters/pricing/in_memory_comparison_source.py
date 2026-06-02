"""In-memory comparison source fallback for pricing workflows."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.pricing import PricingComparable
from src.use_cases.pricing.ports import PricingBrief, PricingComparisonSourcePort


@dataclass
class InMemoryPricingComparisonSource(PricingComparisonSourcePort):
    """Return configured comparable market evidence when SQL catalog truth is unavailable."""

    comparables: dict[str, list[PricingComparable]] = field(default_factory=dict)

    async def list_comparables(self, brief: PricingBrief) -> list[PricingComparable]:
        """Return comparable market evidence for the requested product identifier."""
        return list(self.comparables.get(brief.product_id, []))
