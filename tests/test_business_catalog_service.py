from __future__ import annotations

from decimal import Decimal

import pytest

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessProductStatus,
    CatalogImportStatus,
    CategoryValidationStatus,
    ProductAvailability,
    ProductImageRole,
    ReviewStatus,
    SearchIndexStatus,
)
from src.use_cases.business_catalog.service import (
    AddProductImageRequest,
    BusinessCatalogForbiddenError,
    BusinessCatalogOperationError,
    BusinessCatalogService,
    BusinessCatalogValidationError,
    CreateProductRequest,
    ProductOfferInput,
    UpdateProductRequest,
    UpsertMerchantRequest,
)
from src.use_cases.business_catalog.tenant_partitioning import BusinessCatalogTenantTier
from src.use_cases.product_card.garment_identity_errors import GarmentIdentityAnalysisFailure


class InMemoryBusinessCatalogRepository:
    def __init__(self) -> None:
        self.merchants = {}
        self.products = {}
        self.product_save_count = 0
        self.images = {}
        self.offers = {}
        self.import_jobs = {}
        self.import_errors = []

    async def save_merchant(self, merchant):
        self.merchants[merchant.merchant_id] = merchant
        return merchant

    async def get_merchant_by_owner(self, owner_id: str):
        for merchant in self.merchants.values():
            if merchant.owner_id == owner_id:
                return merchant
        return None

    async def get_merchant(self, merchant_id: str):
        return self.merchants.get(merchant_id)

    async def list_merchants(self):
        return list(self.merchants.values())

    async def save_product(self, product):
        self.product_save_count += 1
        self.products[product.product_id] = product
        return product

    async def get_product(self, product_id: str):
        return self.products.get(product_id)

    async def list_products(self, owner_id: str):
        return [product for product in self.products.values() if product.owner_id == owner_id]

    async def list_pending_products_for_review(self):
        return [product for product in self.products.values() if product.review_status is ReviewStatus.PENDING]

    async def save_product_image(self, image):
        self.images[image.image_id] = image
        return image

    async def list_product_images(self, product_id: str):
        return [image for image in self.images.values() if image.product_id == product_id]

    async def save_offer(self, offer):
        self.offers[offer.offer_id] = offer
        return offer

    async def get_offer(self, product_id: str):
        for offer in self.offers.values():
            if offer.product_id == product_id:
                return offer
        return None

    async def save_import_job(self, job):
        self.import_jobs[job.import_id] = job
        return job

    async def save_import_errors(self, errors):
        self.import_errors.extend(errors)
        return None

    async def get_import_job(self, import_id: str):
        return self.import_jobs.get(import_id)

    async def list_import_errors(self, import_id: str):
        return [error for error in self.import_errors if error.import_id == import_id]

    async def get_catalog_load_metrics(self, merchant: BusinessMerchant):
        products = [product for product in self.products.values() if product.merchant_id == merchant.merchant_id]
        images = [
            image
            for image in self.images.values()
            if any(product.product_id == image.product_id for product in products)
        ]
        imports = [job for job in self.import_jobs.values() if job.merchant_id == merchant.merchant_id]
        return {
            "product_count": len(products),
            "imports_last_30_days": len(imports),
            "largest_import_rows": max((job.total_rows for job in imports), default=0),
            "images_last_30_days": len(images),
            "failed_imports_last_30_days": sum(1 for job in imports if job.status is CatalogImportStatus.FAILED),
        }


class _CategoryAnalyzer:
    def __init__(self, *, visual_category: str = "shirt", confidence: float = 0.94) -> None:
        self.visual_category = visual_category
        self.confidence = confidence
        self.calls = []

    async def analyze_product_image(self, *, job_id: str, object_key: str, content_type: str):
        self.calls.append((job_id, object_key, content_type))
        return {"visual_category": self.visual_category, "confidence": self.confidence}


class _FailingCategoryAnalyzer:
    async def analyze_product_image(self, *, job_id: str, object_key: str, content_type: str):
        raise GarmentIdentityAnalysisFailure(safe_code="auth_error")


@pytest.mark.asyncio
async def test_business_catalog_service_creates_merchant() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())

    merchant = await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(
            display_name="Style Almaty",
            country_code="kz",
            city="Almaty",
        ),
    )

    assert merchant.owner_id == "owner_1"
    assert merchant.country_code == "KZ"


@pytest.mark.asyncio
async def test_business_catalog_service_returns_current_merchant() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(
            display_name="Style Almaty",
            country_code="KZ",
            city="Almaty",
        ),
    )

    merchant = await service.get_merchant("owner_1")

    assert merchant is not None
    assert merchant.display_name == "Style Almaty"


@pytest.mark.asyncio
async def test_business_catalog_service_creates_draft_product_with_offer() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )

    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="kzt",
                availability=ProductAvailability.IN_STOCK,
                delivery_regions=["Almaty"],
            ),
        ),
    )

    assert product.status is BusinessProductStatus.DRAFT
    assert product.review_status is ReviewStatus.NOT_REQUIRED


@pytest.mark.asyncio
async def test_business_catalog_service_blocks_submit_without_primary_image() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )

    with pytest.raises(BusinessCatalogValidationError, match="primary image"):
        await service.submit_product("owner_1", product.product_id)


@pytest.mark.asyncio
async def test_business_catalog_service_submit_sets_pending_review() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.add_product_image(
        "owner_1",
        AddProductImageRequest(
            product_id=product.product_id,
            object_key="catalog/product_1/source.png",
            content_type="image/png",
            size_bytes=1024,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        ),
    )

    submitted = await service.submit_product("owner_1", product.product_id)

    assert submitted.status is BusinessProductStatus.SUBMITTED
    assert submitted.review_status is ReviewStatus.PENDING
    assert submitted.search_index_status is SearchIndexStatus.NOT_INDEXED


@pytest.mark.asyncio
async def test_business_catalog_service_blocks_approval_until_category_validation_passes() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )

    with pytest.raises(BusinessCatalogValidationError, match="category validation"):
        await service.approve_product("admin_1", product.product_id)


@pytest.mark.asyncio
async def test_business_catalog_service_blocks_approval_when_visual_category_mismatches() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="Olive quilted jacket",
            category="outerwear",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("45900"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )

    validated = await service.record_product_category_validation(
        "admin_1",
        product.product_id,
        visual_category="shirt",
        confidence=0.91,
    )

    assert validated.category_validation_status is CategoryValidationStatus.MISMATCH
    with pytest.raises(BusinessCatalogValidationError, match="category mismatch"):
        await service.approve_product("admin_1", product.product_id)


@pytest.mark.asyncio
async def test_business_catalog_service_runs_category_validation_from_primary_image() -> None:
    repository = InMemoryBusinessCatalogRepository()
    analyzer = _CategoryAnalyzer(visual_category="shirt", confidence=0.94)
    service = BusinessCatalogService(repository, category_analyzer=analyzer)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.add_product_image(
        "owner_1",
        AddProductImageRequest(
            product_id=product.product_id,
            object_key="catalog/product_1/primary.png",
            content_type="image/png",
            size_bytes=1024,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        ),
    )

    validated = await service.run_product_category_validation("admin_1", product.product_id)

    assert validated.category_validation_status is CategoryValidationStatus.MATCHED
    assert validated.visual_category == "shirt"
    assert validated.visual_category_confidence == 0.94
    assert analyzer.calls == [
        (
            f"business_catalog_category_validation:{product.product_id}",
            "catalog/product_1/primary.png",
            "image/png",
        )
    ]


@pytest.mark.asyncio
async def test_business_catalog_service_runs_pending_category_validation_batch() -> None:
    repository = InMemoryBusinessCatalogRepository()
    analyzer = _CategoryAnalyzer(visual_category="shirt", confidence=0.94)
    service = BusinessCatalogService(repository, category_analyzer=analyzer)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product_ids = []
    for index in range(2):
        product = await service.create_product(
            "owner_1",
            CreateProductRequest(
                title=f"White oversized shirt {index}",
                category="shirt",
                country_code="KZ",
                city="Almaty",
                offer=ProductOfferInput(
                    price_amount=Decimal("14990"),
                    currency="KZT",
                    availability=ProductAvailability.IN_STOCK,
                ),
            ),
        )
        await service.add_product_image(
            "owner_1",
            AddProductImageRequest(
                product_id=product.product_id,
                object_key=f"catalog/product_{index}/primary.png",
                content_type="image/png",
                size_bytes=1024,
                sha256="a" * 64,
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )
        await service.add_product_image(
            "owner_1",
            AddProductImageRequest(
                product_id=product.product_id,
                object_key=f"catalog/batch_approve_{index}/primary.png",
                content_type="image/png",
                size_bytes=1024,
                sha256="a" * 64,
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )
        await service.submit_product("owner_1", product.product_id)
        product_ids.append(product.product_id)

    result = await service.run_pending_product_category_validations("admin_1", limit=1)

    assert result.requested_limit == 1
    assert result.processed_count == 1
    assert result.validated_count == 1
    assert result.failed_count == 0
    assert result.items[0].product_id == product_ids[0]
    assert result.items[0].product is not None
    assert result.items[0].product.category_validation_status is CategoryValidationStatus.MATCHED
    assert len(analyzer.calls) == 1


@pytest.mark.asyncio
async def test_business_catalog_service_reports_category_analyzer_failure_in_batch() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository, category_analyzer=_FailingCategoryAnalyzer())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.add_product_image(
        "owner_1",
        AddProductImageRequest(
            product_id=product.product_id,
            object_key="catalog/product/primary.png",
            content_type="image/png",
            size_bytes=1024,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        ),
    )
    await service.submit_product("owner_1", product.product_id)

    result = await service.run_pending_product_category_validations("admin_1", limit=1)

    assert result.processed_count == 1
    assert result.validated_count == 0
    assert result.failed_count == 1
    assert result.items[0].product_id == product.product_id
    assert result.items[0].status == "failed"
    assert result.items[0].error_message == "Product category validation agent failed: auth_error"


@pytest.mark.asyncio
async def test_business_catalog_service_maps_category_analyzer_failure_to_operation_error() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository, category_analyzer=_FailingCategoryAnalyzer())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.add_product_image(
        "owner_1",
        AddProductImageRequest(
            product_id=product.product_id,
            object_key="catalog/product/primary.png",
            content_type="image/png",
            size_bytes=1024,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        ),
    )
    await service.submit_product("owner_1", product.product_id)

    with pytest.raises(BusinessCatalogOperationError) as exc_info:
        await service.run_product_category_validation("admin_1", product.product_id)

    assert str(exc_info.value) == "Product category validation agent failed: auth_error"
    assert exc_info.value.safe_code == "business_catalog_category_validation_agent_failed"


@pytest.mark.asyncio
async def test_business_catalog_service_approve_marks_validated_product_pending_search_index() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.record_product_category_validation(
        "admin_1",
        product.product_id,
        visual_category="shirt",
        confidence=0.93,
    )

    await service.record_product_category_validation(
        "admin_1",
        product.product_id,
        visual_category="shirt",
        confidence=0.93,
    )
    await service.record_product_category_validation(
        "admin_1",
        product.product_id,
        visual_category="shirt",
        confidence=0.93,
    )
    await service.record_product_category_validation(
        "admin_1",
        product.product_id,
        visual_category="shirt",
        confidence=0.93,
    )
    approved = await service.approve_product("admin_1", product.product_id)

    assert approved.status is BusinessProductStatus.ACTIVE
    assert approved.review_status is ReviewStatus.APPROVED
    assert approved.search_index_status is SearchIndexStatus.PENDING
    assert approved.search_index_error is None


@pytest.mark.asyncio
async def test_business_catalog_service_approves_matched_pending_products_batch() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product_ids = []
    for index in range(2):
        product = await service.create_product(
            "owner_1",
            CreateProductRequest(
                title=f"White oversized shirt {index}",
                category="shirt",
                country_code="KZ",
                city="Almaty",
                offer=ProductOfferInput(
                    price_amount=Decimal("14990"),
                    currency="KZT",
                    availability=ProductAvailability.IN_STOCK,
                ),
            ),
        )
        await service.add_product_image(
            "owner_1",
            AddProductImageRequest(
                product_id=product.product_id,
                object_key=f"catalog/batch_approve_{index}/primary.png",
                content_type="image/png",
                size_bytes=1024,
                sha256="a" * 64,
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )
        await service.submit_product("owner_1", product.product_id)
        await service.record_product_category_validation(
            "admin_1",
            product.product_id,
            visual_category="shirt" if index == 0 else "outerwear",
            confidence=0.94,
        )
        product_ids.append(product.product_id)

    result = await service.approve_matched_pending_products("admin_1", limit=10)

    assert result.requested_limit == 10
    assert result.processed_count == 1
    assert result.approved_count == 1
    assert result.failed_count == 0
    assert result.items[0].product_id == product_ids[0]
    assert result.items[0].product is not None
    assert result.items[0].product.review_status is ReviewStatus.APPROVED
    assert result.items[0].product.search_index_status is SearchIndexStatus.PENDING
    assert (await repository.get_product(product_ids[1])).review_status is ReviewStatus.PENDING


@pytest.mark.asyncio
async def test_business_catalog_service_admin_archive_removes_product_from_pending_review() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="Acceptance cleanup shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.add_product_image(
        "owner_1",
        AddProductImageRequest(
            product_id=product.product_id,
            object_key="catalog/archive/primary.png",
            content_type="image/png",
            size_bytes=1024,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        ),
    )
    await service.submit_product("owner_1", product.product_id)

    archived = await service.archive_product_as_admin("admin_1", product.product_id)
    pending = await service.list_pending_products_for_review()

    assert archived.status is BusinessProductStatus.ARCHIVED
    assert archived.review_status is ReviewStatus.NOT_REQUIRED
    assert archived.search_index_status is SearchIndexStatus.NOT_INDEXED
    assert all(item.product_id != product.product_id for item in pending)


@pytest.mark.asyncio
async def test_business_catalog_service_retry_search_index_marks_failed_product_pending() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.record_product_category_validation(
        "admin_1",
        product.product_id,
        visual_category="shirt",
        confidence=0.93,
    )
    approved = await service.approve_product("admin_1", product.product_id)
    await repository.save_product(
        approved.model_copy(
            update={
                "search_index_status": SearchIndexStatus.FAILED,
                "search_index_error": "qdrant unavailable",
            }
        )
    )

    retry = await service.retry_product_search_index(admin_actor_id="admin_1", product_id=product.product_id)

    assert retry.search_index_status is SearchIndexStatus.PENDING
    assert retry.search_index_error is None
    assert retry.search_indexed_at is None


@pytest.mark.asyncio
async def test_business_catalog_service_blocks_cross_owner_access() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )

    with pytest.raises(BusinessCatalogForbiddenError):
        await service.get_product("owner_2", product.product_id)


@pytest.mark.asyncio
async def test_business_catalog_service_updates_owned_product() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )

    updated = await service.update_product(
        "owner_1",
        product.product_id,
        UpdateProductRequest(
            title="Linen summer shirt",
            category="shirt",
            description="Lightweight oversize fit.",
            country_code="KZ",
            city="Astana",
            offer=ProductOfferInput(
                price_amount=Decimal("16990"),
                currency="KZT",
                availability=ProductAvailability.PREORDER,
                delivery_regions=["Astana"],
            ),
        ),
    )

    assert updated.title == "Linen summer shirt"
    assert updated.city == "Astana"


@pytest.mark.asyncio
async def test_business_catalog_service_update_approved_product_marks_search_index_pending() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    await service.record_product_category_validation(
        "admin_1",
        product.product_id,
        visual_category="shirt",
        confidence=0.93,
    )
    approved = await service.approve_product("admin_1", product.product_id)
    await repository.save_product(approved.model_copy(update={"search_index_status": SearchIndexStatus.INDEXED}))

    updated = await service.update_product(
        "owner_1",
        product.product_id,
        UpdateProductRequest(
            title="Updated white oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("15990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )

    assert updated.search_index_status is SearchIndexStatus.PENDING
    assert updated.search_indexed_at is None
    assert updated.category_validation_status is CategoryValidationStatus.NOT_CHECKED


@pytest.mark.asyncio
async def test_business_catalog_service_imports_csv_with_row_errors() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )

    job, errors = await service.import_products_from_csv(
        "owner_1",
        "products.csv",
        (
            "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
            "White shirt,shirt,14990,KZT,KZ,Almaty,in_stock,https://example.com/shirt,Almaty\n"
            "Bad price,shirt,-1,KZT,KZ,Almaty,in_stock,https://example.com/bad,Almaty\n"
        ),
    )

    assert job.status is CatalogImportStatus.COMPLETED_WITH_ERRORS
    assert job.accepted_rows == 1
    assert job.rejected_rows == 1
    assert errors[0].safe_code == "invalid_price"
    assert len(await repository.list_products("owner_1")) == 1


@pytest.mark.asyncio
async def test_business_catalog_service_lists_merchant_tier_cards_with_recommendations() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )

    cards = await service.list_merchant_tier_cards()

    assert cards[0].merchant.display_name == "Style Almaty"
    assert cards[0].assigned_tier is BusinessCatalogTenantTier.STANDARD
    assert cards[0].recommended_tier is BusinessCatalogTenantTier.STANDARD
    assert cards[0].hot_account_mode is False


@pytest.mark.asyncio
async def test_business_catalog_service_assigns_merchant_tier_with_admin_reason() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository)
    merchant = await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )

    card = await service.assign_merchant_tier(
        admin_actor_id="admin_1",
        merchant_id=merchant.merchant_id,
        assigned_tier=BusinessCatalogTenantTier.LARGE,
        reason="Client imports large catalogs.",
    )

    saved = await repository.get_merchant(merchant.merchant_id)
    assert card.assigned_tier is BusinessCatalogTenantTier.LARGE
    assert card.hot_account_mode is True
    assert saved.assigned_tier == "large"
    assert saved.tier_assigned_reason == "Client imports large catalogs."
    assert saved.tier_assigned_by == "admin_1"
