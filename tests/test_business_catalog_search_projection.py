from __future__ import annotations

from decimal import Decimal

from src.domain.business_catalog import (
    BusinessProduct,
    BusinessProductOffer,
    BusinessProductStatus,
    ProductAvailability,
    ReviewStatus,
)
from src.use_cases.business_catalog.search_projection import (
    BusinessCatalogSearchProjector,
    project_business_product_for_search,
)
from src.adapters.business_catalog.in_memory_repository import InMemoryBusinessCatalogRepository
from src.domain.similar_search import SimilarityQueryProfile


async def test_in_memory_catalog_search_returns_only_approved_local_matches() -> None:
    repository = InMemoryBusinessCatalogRepository()
    approved = _product("product_active", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED)
    draft = _product("product_draft", BusinessProductStatus.DRAFT, ReviewStatus.NOT_REQUIRED)
    await repository.save_product(approved)
    await repository.save_product(draft)
    await repository.save_offer(_offer("product_active"))
    await repository.save_offer(_offer("product_draft"))

    matches = await repository.search_approved_matches(
        profile=SimilarityQueryProfile(embedding_input="white oversized shirt", category="shirt"),
        limit=10,
    )

    assert [match.product.product_id for match in matches] == ["product_active"]
    assert matches[0].offer.marketplace == "local_catalog"


async def test_in_memory_catalog_search_broadens_when_agent_category_is_more_specific() -> None:
    repository = InMemoryBusinessCatalogRepository()
    approved = _product("product_active", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED)
    await repository.save_product(approved)
    await repository.save_offer(_offer("product_active"))

    matches = await repository.search_approved_matches(
        profile=SimilarityQueryProfile(
            embedding_input="garment_type: button-up shirt; color: white; silhouette: oversized shirt",
            category="button-up shirt",
        ),
        limit=10,
    )

    assert [match.product.product_id for match in matches] == ["product_active"]


async def test_in_memory_repository_lists_approved_search_records_for_reindex() -> None:
    repository = InMemoryBusinessCatalogRepository()
    active = _product("product_active", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED)
    draft = _product("product_draft", BusinessProductStatus.DRAFT, ReviewStatus.NOT_REQUIRED)
    await repository.save_product(active)
    await repository.save_product(draft)
    await repository.save_offer(_offer("product_active"))
    await repository.save_offer(_offer("product_draft"))

    records = await repository.list_approved_search_records(limit=50)

    assert [record.product_id for record in records] == ["product_active"]
    assert records[0].marketplace_source_type == "local_catalog"


async def test_in_memory_repository_hydrates_only_public_safe_vector_hits() -> None:
    repository = InMemoryBusinessCatalogRepository()
    active = _product("product_active", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED)
    archived = _product("product_archived", BusinessProductStatus.ARCHIVED, ReviewStatus.APPROVED)
    pending = _product("product_pending", BusinessProductStatus.SUBMITTED, ReviewStatus.PENDING)
    await repository.save_product(active)
    await repository.save_product(archived)
    await repository.save_product(pending)
    await repository.save_offer(_offer("product_active"))
    await repository.save_offer(_offer("product_archived"))
    await repository.save_offer(_offer("product_pending"))

    products = await repository.get_products_by_ids(["product_active", "product_archived", "product_pending"])
    offers = await repository.list_offers_for_products(
        ["product_active", "product_archived", "product_pending"],
        marketplace_filters=[],
    )

    assert [product.product_id for product in products] == ["product_active"]
    assert [offer.product_id for offer in offers] == ["product_active"]
    assert offers[0].marketplace == "local_catalog"
    assert offers[0].country_code == "KZ"


def test_search_projection_includes_only_active_approved_products() -> None:
    offer = _offer("product_active")

    projected = [
        project_business_product_for_search(product, offer)
        for product in [
            _product("product_draft", BusinessProductStatus.DRAFT, ReviewStatus.NOT_REQUIRED),
            _product("product_submitted", BusinessProductStatus.SUBMITTED, ReviewStatus.PENDING),
            _product("product_rejected", BusinessProductStatus.REJECTED, ReviewStatus.REJECTED),
            _product("product_archived", BusinessProductStatus.ARCHIVED, ReviewStatus.APPROVED),
            _product("product_active", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED),
        ]
    ]

    visible = [record for record in projected if record is not None]

    assert len(visible) == 1
    assert visible[0].product_id == "product_active"


def test_search_projection_preserves_geo_offer_and_delivery_fields() -> None:
    product = _product("product_1", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED)
    offer = _offer("product_1")

    record = project_business_product_for_search(product, offer)

    assert record is not None
    assert record.country_code == "KZ"
    assert record.city == "Almaty"
    assert record.price_amount == Decimal("14990")
    assert record.currency == "KZT"
    assert record.availability is ProductAvailability.IN_STOCK
    assert str(record.product_url) == "https://example.com/product"
    assert record.delivery_regions == ["Almaty", "Astana"]
    assert record.marketplace_source_type == "local_catalog"
    assert record.source_trust_score == 0.85


def test_search_projection_skips_products_without_sellable_offer() -> None:
    product = _product("product_1", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED)

    record = project_business_product_for_search(product, None)

    assert record is None


def test_search_projector_projects_many_records_without_drafts() -> None:
    projector = BusinessCatalogSearchProjector()
    active = _product("product_active", BusinessProductStatus.ACTIVE, ReviewStatus.APPROVED)
    draft = _product("product_draft", BusinessProductStatus.DRAFT, ReviewStatus.NOT_REQUIRED)

    records = projector.project_many(
        [active, draft],
        {
            "product_active": _offer("product_active"),
            "product_draft": _offer("product_draft"),
        },
    )

    assert [record.product_id for record in records] == ["product_active"]


def _product(product_id: str, status: BusinessProductStatus, review_status: ReviewStatus) -> BusinessProduct:
    return BusinessProduct(
        product_id=product_id,
        merchant_id="merchant_1",
        owner_id="owner_1",
        title="White oversized shirt",
        category="shirt",
        description="Lightweight cotton shirt.",
        country_code="kz",
        city="Almaty",
        status=status,
        review_status=review_status,
        source_type="manual",
    )


def _offer(product_id: str) -> BusinessProductOffer:
    return BusinessProductOffer(
        offer_id=f"offer_{product_id}",
        product_id=product_id,
        price_amount=Decimal("14990"),
        currency="kzt",
        availability=ProductAvailability.IN_STOCK,
        product_url="https://example.com/product",
        delivery_regions=["Almaty", "Astana"],
    )
