"""Deterministic fake product-card generation adapter."""

from __future__ import annotations

from src.domain.product_card import ProductCardDraft, ProductCardGarmentAnalysis, ProductCardRequest
from src.use_cases.product_card.ports import ProductCardGenerationPort


class FakeProductCardGenerationAdapter(ProductCardGenerationPort):
    """Return a deterministic structured product-card draft without calling real AI."""

    async def generate(
        self,
        *,
        request: ProductCardRequest,
        garment_analysis: ProductCardGarmentAnalysis,
    ) -> ProductCardDraft:
        """Build a stable product-card draft from request metadata and stored assets."""
        title = request.title_hint or "Generated product card"
        return ProductCardDraft(
            title=title,
            description=f"Structured product card draft built from validated {garment_analysis.garment_type} facts.",
            bullet_points=[
                f"target channel: {request.target_channel}",
                f"brand tone: {request.brand_tone}",
            ],
            attributes={"garment_type": garment_analysis.garment_type},
        )
