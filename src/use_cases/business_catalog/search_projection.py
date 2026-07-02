"""Search projection rules for approved seller catalog products."""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field, HttpUrl

from src.domain.business_catalog import (
    BusinessProduct,
    BusinessProductOffer,
    BusinessProductStatus,
    ProductAvailability,
    ReviewStatus,
    StrictBusinessCatalogModel,
)


class BusinessCatalogSearchRecord(StrictBusinessCatalogModel):
    """Public-search-safe representation of one approved catalog product."""

    product_id: str = Field(min_length=1, max_length=128)
    merchant_id: str = Field(min_length=1, max_length=128)
    owner_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    source_type: str = Field(min_length=1, max_length=64)
    price_amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    availability: ProductAvailability
    product_url: HttpUrl | None = None
    delivery_regions: list[str] = Field(default_factory=list)
    marketplace_source_type: str = Field(default="local_catalog")
    source_trust_score: float = Field(default=0.85, ge=0, le=1)


class BusinessCatalogSearchProjector:
    """Project approved business products into future marketplace/search hydration records."""

    def project(
        self,
        product: BusinessProduct,
        offer: BusinessProductOffer | None,
    ) -> BusinessCatalogSearchRecord | None:
        """Return a public-search record only when product review and offer state are safe."""

        return project_business_product_for_search(product, offer)

    def project_many(
        self,
        products: list[BusinessProduct],
        offers_by_product_id: dict[str, BusinessProductOffer],
    ) -> list[BusinessCatalogSearchRecord]:
        """Return safe search records while preserving input order."""

        records: list[BusinessCatalogSearchRecord] = []
        for product in products:
            record = self.project(product, offers_by_product_id.get(product.product_id))
            if record is not None:
                records.append(record)
        return records


def project_business_product_for_search(
    product: BusinessProduct,
    offer: BusinessProductOffer | None,
) -> BusinessCatalogSearchRecord | None:
    """Project one catalog product only after admin approval and active product status."""

    if product.status is not BusinessProductStatus.ACTIVE:
        return None
    if product.review_status is not ReviewStatus.APPROVED:
        return None
    if offer is None:
        return None
    if offer.product_id != product.product_id:
        return None
    return BusinessCatalogSearchRecord(
        product_id=product.product_id,
        merchant_id=product.merchant_id,
        owner_id=product.owner_id,
        title=product.title,
        category=product.category,
        description=product.description,
        country_code=product.country_code,
        city=product.city,
        source_type=product.source_type,
        price_amount=offer.price_amount,
        currency=offer.currency,
        availability=offer.availability,
        product_url=offer.product_url,
        delivery_regions=list(offer.delivery_regions),
        marketplace_source_type="local_catalog",
        source_trust_score=0.85,
    )
