"""Application service for seller-owned B2B product catalog workflows."""

from __future__ import annotations

from hashlib import sha256
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessMerchantStatus,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductOffer,
    BusinessProductStatus,
    CatalogImportJob,
    CatalogImportRowError,
    CatalogImportStatus,
    CategoryValidationStatus,
    ProductAvailability,
    ProductImageRole,
    ReviewStatus,
    SearchIndexStatus,
    utc_now,
)
from src.domain.garment_category import canonicalize_garment_category
from src.use_cases.business_catalog.backpressure import BusinessCatalogBackpressurePolicy
from src.use_cases.business_catalog.import_parser import parse_business_catalog_csv
from src.use_cases.business_catalog.idempotency import (
    BusinessCatalogIdempotencyStorePort,
    run_idempotent,
    scoped_idempotency_key,
)
from src.use_cases.business_catalog.ports import (
    BusinessCatalogCategoryAnalysis,
    BusinessCatalogCategoryAnalysisPort,
    BusinessCatalogFileStoragePort,
    BusinessCatalogRepositoryPort,
)
from src.use_cases.business_catalog.tenant_partitioning import (
    BusinessCatalogLoadMetrics,
    BusinessCatalogTenantTier,
    TenantPartitionPolicy,
)
from src.use_cases.business_catalog.tier_admin import BusinessMerchantTierCard
from src.use_cases.product_card.garment_identity_errors import GarmentIdentityAnalysisFailure


ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_PRODUCT_IMAGE_BYTES = 10 * 1024 * 1024


class BusinessCatalogError(RuntimeError):
    """Base business catalog use-case error."""


class BusinessCatalogForbiddenError(BusinessCatalogError):
    """Raised when an owner attempts to access another owner's catalog data."""


class BusinessCatalogNotFoundError(BusinessCatalogError):
    """Raised when requested catalog data does not exist."""


class BusinessCatalogValidationError(BusinessCatalogError):
    """Raised when catalog workflow rules block the requested transition."""


class BusinessCatalogOperationError(BusinessCatalogError):
    """Raised when catalog infrastructure operation fails without silent success."""

    def __init__(
        self,
        message: str,
        *,
        safe_code: str,
        cleanup_required: bool = False,
        cleanup_object_key: str | None = None,
    ) -> None:
        """Store structured operation failure details."""

        super().__init__(message)
        self.safe_code = safe_code
        self.cleanup_required = cleanup_required
        self.cleanup_object_key = cleanup_object_key


class BusinessCatalogBackpressureError(BusinessCatalogError):
    """Raised when a catalog request exceeds workload tier limits."""

    def __init__(self, message: str, *, limit_name: str, limit_value: int, actual_value: int) -> None:
        """Store structured backpressure details."""

        super().__init__(message)
        self.safe_code = "business_catalog_backpressure"
        self.limit_name = limit_name
        self.limit_value = limit_value
        self.actual_value = actual_value


class UpsertMerchantRequest(BaseModel):
    """Backend-owned request for creating or updating a merchant profile."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    contact_email: str | None = Field(default=None, max_length=255)
    instagram_url: HttpUrl | None = None
    website_url: HttpUrl | None = None


class ProductOfferInput(BaseModel):
    """Backend-owned request fragment for one product offer."""

    model_config = ConfigDict(extra="forbid")

    price_amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    availability: ProductAvailability
    product_url: HttpUrl | None = None
    delivery_regions: list[str] = Field(default_factory=list)


class CreateProductRequest(BaseModel):
    """Backend-owned request for creating a draft catalog product."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    offer: ProductOfferInput
    source_type: str = Field(default="manual", min_length=1, max_length=64)


class UpdateProductRequest(BaseModel):
    """Backend-owned request for editing product metadata and offer."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    offer: ProductOfferInput


class AddProductImageRequest(BaseModel):
    """Backend-owned request for attaching a stored image to a product."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=128)
    object_key: str = Field(min_length=1, max_length=1024)
    content_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: ProductImageRole
    sort_order: int = Field(ge=0)


class UploadProductImageRequest(BaseModel):
    """Backend-owned request for validating and storing one product image upload."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=128)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    content: bytes = Field(min_length=1)
    role: ProductImageRole
    sort_order: int = Field(ge=0)


class BulkCategoryValidationItem(BaseModel):
    """One item-level result from an admin bulk category validation run."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=128)
    status: str = Field(pattern=r"^(validated|failed)$")
    product: BusinessProduct | None = None
    error_message: str | None = Field(default=None, max_length=1000)


class BulkCategoryValidationResult(BaseModel):
    """Bounded admin bulk category validation summary."""

    model_config = ConfigDict(extra="forbid")

    requested_limit: int = Field(ge=1, le=25)
    processed_count: int = Field(ge=0)
    validated_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    items: list[BulkCategoryValidationItem] = Field(default_factory=list)


class BulkProductApprovalItem(BaseModel):
    """One item-level result from an admin bulk approval run."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=128)
    status: str = Field(pattern=r"^(approved|failed)$")
    product: BusinessProduct | None = None
    error_message: str | None = Field(default=None, max_length=1000)


class BulkProductApprovalResult(BaseModel):
    """Bounded admin bulk approval summary."""

    model_config = ConfigDict(extra="forbid")

    requested_limit: int = Field(ge=1, le=25)
    processed_count: int = Field(ge=0)
    approved_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    items: list[BulkProductApprovalItem] = Field(default_factory=list)


class BusinessCatalogService:
    """Coordinate seller catalog lifecycle without binding to a concrete database."""

    def __init__(
        self,
        repository: BusinessCatalogRepositoryPort,
        *,
        file_storage: BusinessCatalogFileStoragePort | None = None,
        category_analyzer: BusinessCatalogCategoryAnalysisPort | None = None,
        tenant_partition_policy: TenantPartitionPolicy | None = None,
        idempotency_store: BusinessCatalogIdempotencyStorePort | None = None,
        backpressure_policy: BusinessCatalogBackpressurePolicy | None = None,
    ) -> None:
        """Store explicit persistence boundary."""

        self._repository = repository
        self._file_storage = file_storage
        self._category_analyzer = category_analyzer
        self._tenant_partition_policy = tenant_partition_policy or TenantPartitionPolicy()
        self._idempotency_store = idempotency_store
        self._backpressure_policy = backpressure_policy or BusinessCatalogBackpressurePolicy()

    async def upsert_merchant(self, owner_id: str, request: UpsertMerchantRequest) -> BusinessMerchant:
        """Create or update the merchant profile owned by one workspace owner."""

        existing = await self._repository.get_merchant_by_owner(owner_id)
        merchant = BusinessMerchant(
            merchant_id=existing.merchant_id if existing else _new_id("merchant"),
            owner_id=owner_id,
            display_name=request.display_name,
            legal_name=request.legal_name,
            country_code=request.country_code,
            city=request.city,
            contact_email=request.contact_email,
            instagram_url=request.instagram_url,
            website_url=request.website_url,
            status=existing.status if existing else BusinessMerchantStatus.DRAFT,
            created_at=existing.created_at if existing else utc_now(),
        )
        return await self._repository.save_merchant(merchant)

    async def get_merchant(self, owner_id: str) -> BusinessMerchant | None:
        """Return the merchant profile owned by one workspace owner."""

        return await self._repository.get_merchant_by_owner(owner_id)

    async def create_product(self, owner_id: str, request: CreateProductRequest) -> BusinessProduct:
        """Create a draft product and its initial sellable offer."""

        merchant = await self._require_merchant(owner_id)
        product = BusinessProduct(
            product_id=_new_id("product"),
            merchant_id=merchant.merchant_id,
            owner_id=owner_id,
            title=request.title,
            category=request.category,
            description=request.description,
            country_code=request.country_code,
            city=request.city,
            status=BusinessProductStatus.DRAFT,
            review_status=ReviewStatus.NOT_REQUIRED,
            source_type=request.source_type,
        )
        offer = BusinessProductOffer(
            offer_id=_new_id("offer"),
            product_id=product.product_id,
            price_amount=request.offer.price_amount,
            currency=request.offer.currency,
            availability=request.offer.availability,
            product_url=request.offer.product_url,
            delivery_regions=request.offer.delivery_regions,
        )
        await self._repository.save_product(product)
        await self._repository.save_offer(offer)
        return product

    async def update_product(
        self,
        owner_id: str,
        product_id: str,
        request: UpdateProductRequest,
    ) -> BusinessProduct:
        """Update owner product metadata and its current offer."""

        product = await self._require_owned_product(owner_id, product_id)
        search_index_update = {}
        if product.status is BusinessProductStatus.ACTIVE and product.review_status is ReviewStatus.APPROVED:
            search_index_update = {
                "search_index_status": SearchIndexStatus.PENDING,
                "search_index_error": None,
                "search_indexed_at": None,
            }
        updated = product.model_copy(
            update={
                "title": request.title,
                "category": request.category,
                "description": request.description,
                "country_code": request.country_code.strip().upper(),
                "city": request.city,
                "category_validation_status": CategoryValidationStatus.NOT_CHECKED,
                "category_validation_reason": None,
                "visual_category": None,
                "visual_category_confidence": None,
                "category_validated_at": None,
                **search_index_update,
            }
        )
        existing_offer = await self._repository.get_offer(product_id)
        offer = BusinessProductOffer(
            offer_id=existing_offer.offer_id if existing_offer else _new_id("offer"),
            product_id=product_id,
            price_amount=request.offer.price_amount,
            currency=request.offer.currency,
            availability=request.offer.availability,
            product_url=request.offer.product_url,
            delivery_regions=request.offer.delivery_regions,
        )
        await self._repository.save_offer(offer)
        return await self._repository.save_product(updated)

    async def add_product_image(self, owner_id: str, request: AddProductImageRequest) -> BusinessProductImage:
        """Attach already stored product image metadata after owner validation."""

        product = await self._require_owned_product(owner_id, request.product_id)
        image = BusinessProductImage(
            image_id=_new_id("image"),
            product_id=product.product_id,
            object_key=request.object_key,
            content_type=request.content_type,
            size_bytes=request.size_bytes,
            sha256=request.sha256,
            role=request.role,
            sort_order=request.sort_order,
        )
        saved_image = await self._repository.save_product_image(image)
        await self._repository.save_product(
            product.model_copy(
                update={
                    "category_validation_status": CategoryValidationStatus.NOT_CHECKED,
                    "category_validation_reason": None,
                    "visual_category": None,
                    "visual_category_confidence": None,
                    "category_validated_at": None,
                    "updated_at": utc_now(),
                }
            )
        )
        return saved_image

    async def upload_product_image(
        self,
        owner_id: str,
        request: UploadProductImageRequest,
        *,
        idempotency_key: str | None = None,
    ) -> BusinessProductImage:
        """Validate, store and attach one product image upload."""

        async def operation() -> BusinessProductImage:
            if self._file_storage is None:
                raise BusinessCatalogValidationError("Business catalog file storage is not configured.")
            content_type = request.content_type.strip().lower()
            if content_type not in ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES:
                raise BusinessCatalogValidationError("Unsupported product image type.")
            size_bytes = len(request.content)
            if size_bytes > MAX_PRODUCT_IMAGE_BYTES:
                raise BusinessCatalogValidationError("Product image exceeds the maximum size of 10 MB.")
            await self._require_owned_product(owner_id, request.product_id)
            merchant = await self._require_merchant(owner_id)
            existing_images = await self._repository.list_product_images(request.product_id)
            self._backpressure_policy.validate_image_count(
                tier=BusinessCatalogTenantTier(merchant.assigned_tier),
                existing_count=len(existing_images),
            )
            try:
                object_key = await self._file_storage.save_upload(
                    owner_id=owner_id,
                    filename=request.filename,
                    content_type=content_type,
                    content=request.content,
                )
            except Exception as exc:
                raise BusinessCatalogOperationError(
                    "Product image storage failed.",
                    safe_code="business_catalog_storage_failed",
                ) from exc
            try:
                return await self.add_product_image(
                    owner_id,
                    AddProductImageRequest(
                        product_id=request.product_id,
                        object_key=object_key,
                        content_type=content_type,
                        size_bytes=size_bytes,
                        sha256=sha256(request.content).hexdigest(),
                        role=request.role,
                        sort_order=request.sort_order,
                    ),
                )
            except Exception as exc:
                raise BusinessCatalogOperationError(
                    "Product image metadata persistence failed after storage.",
                    safe_code="business_catalog_metadata_failed",
                    cleanup_required=True,
                    cleanup_object_key=object_key,
                ) from exc

        return await run_idempotent(
            store=self._idempotency_store,
            operation_key=scoped_idempotency_key(
                owner_id=owner_id,
                operation=f"product-image:{request.product_id}",
                idempotency_key=idempotency_key,
            ),
            operation=operation,
        )

    async def import_products_from_csv(
        self,
        owner_id: str,
        filename: str,
        content: str,
        *,
        idempotency_key: str | None = None,
    ) -> tuple[CatalogImportJob, list[CatalogImportRowError]]:
        """Parse one CSV import, persist accepted products and row-level errors."""

        async def operation() -> tuple[CatalogImportJob, list[CatalogImportRowError]]:
            merchant = await self._require_merchant(owner_id)
            row_count = _csv_data_row_count(content)
            self._backpressure_policy.validate_csv(
                tier=BusinessCatalogTenantTier(merchant.assigned_tier),
                row_count=row_count,
                size_bytes=len(content.encode("utf-8")),
            )
            parsed = parse_business_catalog_csv(content)
            accepted_rows = 0
            for row in parsed.rows:
                await self.create_product(
                    owner_id,
                    CreateProductRequest(
                        title=row.title,
                        category=row.category,
                        country_code=row.country_code,
                        city=row.city,
                        offer=ProductOfferInput(
                            price_amount=row.price_amount,
                            currency=row.currency,
                            availability=row.availability,
                            product_url=row.product_url,
                            delivery_regions=row.delivery_regions,
                        ),
                        source_type="csv_import",
                    ),
                )
                accepted_rows += 1
            import_id = _new_id("import")
            errors = [
                CatalogImportRowError(
                    import_id=import_id,
                    row_number=error.row_number,
                    field_name=error.field_name,
                    safe_code=error.safe_code,
                    message=error.message,
                )
                for error in parsed.errors
            ]
            total_rows = accepted_rows + len(errors)
            status = CatalogImportStatus.COMPLETED
            if errors and accepted_rows:
                status = CatalogImportStatus.COMPLETED_WITH_ERRORS
            elif errors:
                status = CatalogImportStatus.FAILED
            now = utc_now()
            job = CatalogImportJob(
                import_id=import_id,
                merchant_id=merchant.merchant_id,
                owner_id=owner_id,
                filename=filename,
                status=status,
                total_rows=total_rows,
                accepted_rows=accepted_rows,
                rejected_rows=len(errors),
                error_summary=f"{len(errors)} rows rejected." if errors else None,
                created_at=now,
                completed_at=now,
            )
            await self._repository.save_import_job(job)
            if errors:
                try:
                    await self._repository.save_import_errors(errors)
                except Exception:
                    failed_job = job.model_copy(
                        update={
                            "status": CatalogImportStatus.FAILED,
                            "error_summary": "Failed to persist import row errors.",
                            "completed_at": utc_now(),
                        }
                    )
                    await self._repository.save_import_job(failed_job)
                    return failed_job, errors
            return job, errors

        return await run_idempotent(
            store=self._idempotency_store,
            operation_key=scoped_idempotency_key(
                owner_id=owner_id,
                operation="catalog-import",
                idempotency_key=idempotency_key,
            ),
            operation=operation,
        )

    async def get_import_job(self, owner_id: str, import_id: str) -> CatalogImportJob | None:
        """Return one import job after owner validation."""

        getter = getattr(self._repository, "get_import_job", None)
        if getter is None:
            return None
        job = await getter(import_id)
        if job is None:
            return None
        if job.owner_id != owner_id:
            raise BusinessCatalogForbiddenError("Catalog import belongs to another workspace owner.")
        return job

    async def list_import_errors(self, owner_id: str, import_id: str) -> list[CatalogImportRowError]:
        """Return row-level import errors after owner validation."""

        job = await self.get_import_job(owner_id, import_id)
        if job is None:
            raise BusinessCatalogNotFoundError(f"Catalog import {import_id!r} was not found.")
        getter = getattr(self._repository, "list_import_errors", None)
        if getter is None:
            return []
        return await getter(import_id)

    async def submit_product(
        self,
        owner_id: str,
        product_id: str,
        *,
        idempotency_key: str | None = None,
    ) -> BusinessProduct:
        """Move a draft product into admin review after required readiness checks."""

        async def operation() -> BusinessProduct:
            product = await self._require_owned_product(owner_id, product_id)
            images = await self._repository.list_product_images(product_id)
            if not any(image.role is ProductImageRole.PRIMARY for image in images):
                raise BusinessCatalogValidationError("Product requires a primary image before review submission.")
            offer = await self._repository.get_offer(product_id)
            if offer is None:
                raise BusinessCatalogValidationError("Product requires a sellable offer before review submission.")
            submitted = product.model_copy(
                update={
                    "status": BusinessProductStatus.SUBMITTED,
                    "review_status": ReviewStatus.PENDING,
                    "review_reason": None,
                }
            )
            return await self._repository.save_product(submitted)

        return await run_idempotent(
            store=self._idempotency_store,
            operation_key=scoped_idempotency_key(
                owner_id=owner_id,
                operation=f"submit-product:{product_id}",
                idempotency_key=idempotency_key,
            ),
            operation=operation,
        )

    async def get_product(self, owner_id: str, product_id: str) -> BusinessProduct:
        """Return one product after owner validation."""

        return await self._require_owned_product(owner_id, product_id)

    async def list_products(self, owner_id: str) -> list[BusinessProduct]:
        """Return products visible to the requested owner."""

        return await self._repository.list_products(owner_id)

    async def list_pending_products_for_review(self) -> list[BusinessProduct]:
        """Return submitted products waiting for admin review."""

        lister = getattr(self._repository, "list_pending_products_for_review", None)
        if lister is None:
            return []
        return await lister()

    async def list_merchant_tier_cards(self) -> list[BusinessMerchantTierCard]:
        """Return merchant workload tier cards for admin review."""

        lister = getattr(self._repository, "list_merchants", None)
        if lister is None:
            return []
        merchants = await lister()
        cards: list[BusinessMerchantTierCard] = []
        for merchant in merchants:
            cards.append(await self._merchant_tier_card(merchant))
        return cards

    async def assign_merchant_tier(
        self,
        *,
        admin_actor_id: str,
        merchant_id: str,
        assigned_tier: BusinessCatalogTenantTier,
        reason: str,
    ) -> BusinessMerchantTierCard:
        """Persist one admin-approved merchant tier assignment."""

        _require_actor(admin_actor_id)
        if not reason.strip():
            raise BusinessCatalogValidationError("Merchant tier assignment requires a reason.")
        getter = getattr(self._repository, "get_merchant", None)
        if getter is None:
            raise BusinessCatalogValidationError("Business merchant tier storage is not configured.")
        merchant = await getter(merchant_id)
        if merchant is None:
            raise BusinessCatalogNotFoundError(f"Merchant {merchant_id!r} was not found.")
        updated = merchant.model_copy(
            update={
                "assigned_tier": assigned_tier.value,
                "tier_assigned_reason": reason.strip(),
                "tier_assigned_by": admin_actor_id,
                "tier_assigned_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        saved = await self._repository.save_merchant(updated)
        return await self._merchant_tier_card(saved)

    async def approve_product(self, admin_actor_id: str, product_id: str) -> BusinessProduct:
        """Approve a submitted product for future search/public projections."""

        _require_actor(admin_actor_id)
        product = await self._require_product(product_id)
        self._require_category_validation_match(product)
        approved = product.model_copy(
            update={
                "status": BusinessProductStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "review_reason": None,
                "search_index_status": SearchIndexStatus.PENDING,
                "search_index_error": None,
                "search_indexed_at": None,
            }
        )
        return await self._repository.save_product(approved)

    async def approve_matched_pending_products(
        self,
        admin_actor_id: str,
        *,
        limit: int = 10,
    ) -> BulkProductApprovalResult:
        """Approve a bounded batch of pending products that already passed category validation."""

        _require_actor(admin_actor_id)
        if limit < 1 or limit > 25:
            raise BusinessCatalogValidationError("Bulk product approval limit must be between 1 and 25.")
        pending_products = await self.list_pending_products_for_review()
        candidates = [
            product
            for product in pending_products
            if product.category_validation_status is CategoryValidationStatus.MATCHED
        ][:limit]
        items: list[BulkProductApprovalItem] = []
        for product in candidates:
            try:
                approved = await self.approve_product(admin_actor_id, product.product_id)
            except BusinessCatalogError as exc:
                items.append(
                    BulkProductApprovalItem(
                        product_id=product.product_id,
                        status="failed",
                        error_message=str(exc),
                    )
                )
            else:
                items.append(
                    BulkProductApprovalItem(
                        product_id=product.product_id,
                        status="approved",
                        product=approved,
                    )
                )
        return BulkProductApprovalResult(
            requested_limit=limit,
            processed_count=len(items),
            approved_count=sum(1 for item in items if item.status == "approved"),
            failed_count=sum(1 for item in items if item.status == "failed"),
            items=items,
        )

    async def record_product_category_validation(
        self,
        admin_actor_id: str,
        product_id: str,
        *,
        visual_category: str,
        confidence: float,
    ) -> BusinessProduct:
        """Persist visual category validation before admin approval/indexing."""

        _require_actor(admin_actor_id)
        product = await self._require_product(product_id)
        if not visual_category.strip():
            raise BusinessCatalogValidationError("Product category validation requires visual category.")
        if confidence < 0 or confidence > 1:
            raise BusinessCatalogValidationError("Product category validation confidence must be between 0 and 1.")
        status, reason = _evaluate_category_validation(
            declared_category=product.category,
            visual_category=visual_category,
            confidence=confidence,
        )
        validated = product.model_copy(
            update={
                "category_validation_status": status,
                "category_validation_reason": reason,
                "visual_category": visual_category.strip(),
                "visual_category_confidence": confidence,
                "category_validated_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        return await self._repository.save_product(validated)

    async def run_product_category_validation(self, admin_actor_id: str, product_id: str) -> BusinessProduct:
        """Analyze the primary product image and persist category validation."""

        _require_actor(admin_actor_id)
        if self._category_analyzer is None:
            raise BusinessCatalogValidationError("Business catalog category analyzer is not configured.")
        product = await self._require_product(product_id)
        images = await self._repository.list_product_images(product_id)
        primary_images = [image for image in images if image.role is ProductImageRole.PRIMARY]
        if not primary_images:
            raise BusinessCatalogValidationError("Product category validation requires a primary image.")
        primary_images.sort(key=lambda image: (image.sort_order, image.image_id))
        primary_image = primary_images[0]
        try:
            raw_analysis = await self._category_analyzer.analyze_product_image(
                job_id=f"business_catalog_category_validation:{product.product_id}",
                object_key=primary_image.object_key,
                content_type=primary_image.content_type,
            )
        except GarmentIdentityAnalysisFailure as exc:
            raise BusinessCatalogOperationError(
                f"Product category validation agent failed: {exc.safe_code}",
                safe_code="business_catalog_category_validation_agent_failed",
            ) from exc
        analysis = BusinessCatalogCategoryAnalysis.model_validate(raw_analysis)
        return await self.record_product_category_validation(
            admin_actor_id,
            product.product_id,
            visual_category=analysis.visual_category,
            confidence=analysis.confidence,
        )

    async def run_pending_product_category_validations(
        self,
        admin_actor_id: str,
        *,
        limit: int = 10,
    ) -> BulkCategoryValidationResult:
        """Run category validation for a bounded batch of pending products."""

        _require_actor(admin_actor_id)
        if limit < 1 or limit > 25:
            raise BusinessCatalogValidationError("Bulk category validation limit must be between 1 and 25.")
        pending_products = await self.list_pending_products_for_review()
        candidates = [
            product
            for product in pending_products
            if product.category_validation_status is not CategoryValidationStatus.MATCHED
        ][:limit]
        items: list[BulkCategoryValidationItem] = []
        for product in candidates:
            try:
                validated = await self.run_product_category_validation(admin_actor_id, product.product_id)
            except BusinessCatalogError as exc:
                items.append(
                    BulkCategoryValidationItem(
                        product_id=product.product_id,
                        status="failed",
                        error_message=str(exc),
                    )
                )
            else:
                items.append(
                    BulkCategoryValidationItem(
                        product_id=product.product_id,
                        status="validated",
                        product=validated,
                    )
                )
        return BulkCategoryValidationResult(
            requested_limit=limit,
            processed_count=len(items),
            validated_count=sum(1 for item in items if item.status == "validated"),
            failed_count=sum(1 for item in items if item.status == "failed"),
            items=items,
        )

    async def reject_product(self, admin_actor_id: str, product_id: str, reason: str) -> BusinessProduct:
        """Reject a submitted product with an explicit admin reason."""

        _require_actor(admin_actor_id)
        if not reason.strip():
            raise BusinessCatalogValidationError("Product rejection requires a reason.")
        product = await self._require_product(product_id)
        rejected = product.model_copy(
            update={
                "status": BusinessProductStatus.REJECTED,
                "review_status": ReviewStatus.REJECTED,
                "review_reason": reason.strip(),
            }
        )
        return await self._repository.save_product(rejected)

    async def retry_product_search_index(self, admin_actor_id: str, product_id: str) -> BusinessProduct:
        """Schedule one approved product for search reindex after an indexing failure."""

        _require_actor(admin_actor_id)
        product = await self._require_product(product_id)
        if product.status is not BusinessProductStatus.ACTIVE or product.review_status is not ReviewStatus.APPROVED:
            raise BusinessCatalogValidationError("Only active approved products can be scheduled for search indexing.")
        retry = product.model_copy(
            update={
                "search_index_status": SearchIndexStatus.PENDING,
                "search_index_error": None,
                "search_indexed_at": None,
                "updated_at": utc_now(),
            }
        )
        return await self._repository.save_product(retry)

    async def get_public_primary_product_image(self, product_id: str) -> BusinessProductImage | None:
        """Return the primary image for an active approved product visible in search."""

        product = await self._require_product(product_id)
        if product.status is not BusinessProductStatus.ACTIVE or product.review_status is not ReviewStatus.APPROVED:
            return None
        images = await self._repository.list_product_images(product_id)
        primary_images = [image for image in images if image.role is ProductImageRole.PRIMARY]
        if not primary_images:
            return None
        primary_images.sort(key=lambda image: (image.sort_order, image.image_id))
        return primary_images[0]

    async def archive_product(self, owner_id: str, product_id: str) -> BusinessProduct:
        """Archive an owner product without deleting history."""

        product = await self._require_owned_product(owner_id, product_id)
        archived = product.model_copy(update={"status": BusinessProductStatus.ARCHIVED})
        return await self._repository.save_product(archived)

    async def archive_product_as_admin(self, admin_actor_id: str, product_id: str) -> BusinessProduct:
        """Archive any catalog product after explicit admin action."""

        _require_actor(admin_actor_id)
        product = await self._require_product(product_id)
        archived = product.model_copy(
            update={
                "status": BusinessProductStatus.ARCHIVED,
                "review_status": ReviewStatus.NOT_REQUIRED,
                "review_reason": None,
                "search_index_status": SearchIndexStatus.NOT_INDEXED,
                "search_index_error": None,
                "search_indexed_at": None,
                "updated_at": utc_now(),
            }
        )
        return await self._repository.save_product(archived)

    async def _merchant_tier_card(self, merchant: BusinessMerchant) -> BusinessMerchantTierCard:
        metrics = await self._merchant_load_metrics(merchant)
        decision = self._tenant_partition_policy.resolve(
            owner_id=merchant.owner_id,
            merchant_id=merchant.merchant_id,
            assigned_tier=BusinessCatalogTenantTier(merchant.assigned_tier),
            metrics=metrics,
        )
        return BusinessMerchantTierCard(
            merchant=merchant,
            assigned_tier=decision.assigned_tier,
            recommended_tier=decision.recommended_tier,
            recommendation_reasons=decision.recommendation_reasons,
            metrics=metrics,
            queue_partition=decision.queue_partition,
            storage_prefix=decision.storage_prefix,
            rate_limit_bucket=decision.rate_limit_bucket,
            hot_account_mode=decision.hot_account_mode,
        )

    async def _merchant_load_metrics(self, merchant: BusinessMerchant) -> BusinessCatalogLoadMetrics:
        getter = getattr(self._repository, "get_catalog_load_metrics", None)
        if getter is None:
            return BusinessCatalogLoadMetrics(
                product_count=0,
                imports_last_30_days=0,
                largest_import_rows=0,
                images_last_30_days=0,
                failed_imports_last_30_days=0,
            )
        raw_metrics = await getter(merchant)
        if isinstance(raw_metrics, BusinessCatalogLoadMetrics):
            return raw_metrics
        return BusinessCatalogLoadMetrics(**raw_metrics)

    async def _require_merchant(self, owner_id: str) -> BusinessMerchant:
        merchant = await self._repository.get_merchant_by_owner(owner_id)
        if merchant is None:
            raise BusinessCatalogValidationError("Business merchant profile is required before catalog products.")
        return merchant

    async def _require_product(self, product_id: str) -> BusinessProduct:
        product = await self._repository.get_product(product_id)
        if product is None:
            raise BusinessCatalogNotFoundError(f"Product {product_id!r} was not found.")
        return product

    async def _require_owned_product(self, owner_id: str, product_id: str) -> BusinessProduct:
        product = await self._require_product(product_id)
        if product.owner_id != owner_id:
            raise BusinessCatalogForbiddenError("Product belongs to another workspace owner.")
        return product

    def _require_category_validation_match(self, product: BusinessProduct) -> None:
        if product.category_validation_status is CategoryValidationStatus.MATCHED:
            return
        if product.category_validation_status is CategoryValidationStatus.MISMATCH:
            raise BusinessCatalogValidationError(
                f"Product category mismatch: {product.category_validation_reason or 'visual category differs'}"
            )
        if product.category_validation_status is CategoryValidationStatus.UNCERTAIN:
            raise BusinessCatalogValidationError(
                f"Product category validation is uncertain: {product.category_validation_reason or 'low confidence'}"
            )
        raise BusinessCatalogValidationError("Product category validation is required before approval.")


def _new_id(prefix: str) -> str:
    """Create opaque ids without leaking database implementation details."""

    return f"{prefix}_{uuid4().hex}"


def _csv_data_row_count(content: str) -> int:
    """Count non-empty CSV data rows without running full row validation."""

    lines = [line for line in content.splitlines() if line.strip()]
    if not lines:
        return 0
    return max(len(lines) - 1, 0)


def _evaluate_category_validation(
    *,
    declared_category: str,
    visual_category: str,
    confidence: float,
) -> tuple[CategoryValidationStatus, str]:
    """Compare declared catalog category with visual garment analysis."""

    declared = canonicalize_garment_category(declared_category)
    visual = canonicalize_garment_category(visual_category)
    if confidence < 0.7:
        return (
            CategoryValidationStatus.UNCERTAIN,
            f"visual category confidence {confidence:.2f} is below 0.70",
        )
    if declared is None or visual is None:
        return (CategoryValidationStatus.UNCERTAIN, "declared or visual category is missing")
    if declared != visual:
        return (
            CategoryValidationStatus.MISMATCH,
            f"declared category {declared!r} differs from visual category {visual!r}",
        )
    return (CategoryValidationStatus.MATCHED, f"declared category {declared!r} matches visual category {visual!r}")


def _require_actor(actor_id: str) -> None:
    """Ensure admin transitions are attributable."""

    if not actor_id.strip():
        raise BusinessCatalogValidationError("Admin actor id is required.")
