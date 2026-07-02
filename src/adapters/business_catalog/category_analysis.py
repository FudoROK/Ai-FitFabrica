"""Business catalog visual category analysis adapters."""

from __future__ import annotations

from dataclasses import dataclass

from src.use_cases.business_catalog.ports import BusinessCatalogCategoryAnalysis


@dataclass(frozen=True)
class GarmentIdentityBusinessCatalogCategoryAnalyzer:
    """Adapt Garment Identity analysis to the B2B catalog category gate."""

    garment_identity_analyzer: object

    async def analyze_product_image(
        self,
        *,
        job_id: str,
        object_key: str,
        content_type: str,
    ) -> BusinessCatalogCategoryAnalysis:
        """Return the best visual category signal from Garment Identity."""

        analysis = await self.garment_identity_analyzer.analyze(job_id=job_id, asset_keys=[object_key])
        visual_category = getattr(analysis, "taxonomy_parent", None) or getattr(analysis, "garment_type")
        confidence = getattr(analysis, "taxonomy_confidence", None) or getattr(analysis, "confidence")
        return BusinessCatalogCategoryAnalysis(visual_category=visual_category, confidence=confidence)


@dataclass(frozen=True)
class SandboxBusinessCatalogCategoryAnalyzer:
    """Deterministic staging/dev analyzer for exercising catalog orchestration without AI spend."""

    async def analyze_product_image(
        self,
        *,
        job_id: str,
        object_key: str,
        content_type: str,
    ) -> BusinessCatalogCategoryAnalysis:
        """Infer a stable visual category from test asset names only."""

        del job_id, content_type
        lowered_key = object_key.lower()
        if "tshirt" in lowered_key or "t-shirt" in lowered_key or "tee" in lowered_key or "longsleeve" in lowered_key:
            return BusinessCatalogCategoryAnalysis(visual_category="tshirt", confidence=0.96)
        if "dress" in lowered_key:
            return BusinessCatalogCategoryAnalysis(visual_category="dress", confidence=0.96)
        if "skirt" in lowered_key:
            return BusinessCatalogCategoryAnalysis(visual_category="skirt", confidence=0.94)
        if "coat" in lowered_key or "jacket" in lowered_key or "outerwear" in lowered_key or "blazer" in lowered_key:
            return BusinessCatalogCategoryAnalysis(visual_category="outerwear", confidence=0.94)
        if "pants" in lowered_key or "jeans" in lowered_key or "trouser" in lowered_key:
            return BusinessCatalogCategoryAnalysis(visual_category="pants", confidence=0.94)
        if "shirt" in lowered_key:
            return BusinessCatalogCategoryAnalysis(visual_category="shirt", confidence=0.96)
        return BusinessCatalogCategoryAnalysis(visual_category="unknown", confidence=0.1)
