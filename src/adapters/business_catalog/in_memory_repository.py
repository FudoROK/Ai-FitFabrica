"""In-memory business catalog repository for tests and sandbox runtimes."""

from __future__ import annotations

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductOffer,
    BusinessProductStatus,
    CatalogImportJob,
    CatalogImportRowError,
    CatalogImportStatus,
    ProductAvailability,
    ReviewStatus,
    SearchIndexStatus,
    utc_now,
)
from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord, HydratedCatalogMatch, SimilarityQueryProfile
from src.use_cases.business_catalog.search_projection import BusinessCatalogSearchRecord, project_business_product_for_search


class InMemoryBusinessCatalogRepository:
    """Store B2B catalog state in memory for local non-durable runtimes."""

    def __init__(self) -> None:
        """Initialize empty catalog collections."""

        self._merchants: dict[str, BusinessMerchant] = {}
        self._products: dict[str, BusinessProduct] = {}
        self._images: dict[str, BusinessProductImage] = {}
        self._offers: dict[str, BusinessProductOffer] = {}
        self._import_jobs: dict[str, CatalogImportJob] = {}
        self._import_errors: list[CatalogImportRowError] = []

    async def save_merchant(self, merchant: BusinessMerchant) -> BusinessMerchant:
        """Persist a merchant profile."""

        self._merchants[merchant.merchant_id] = merchant
        return merchant

    async def get_merchant_by_owner(self, owner_id: str) -> BusinessMerchant | None:
        """Return the merchant profile owned by one workspace owner."""

        return next((merchant for merchant in self._merchants.values() if merchant.owner_id == owner_id), None)

    async def get_merchant(self, merchant_id: str) -> BusinessMerchant | None:
        """Return one merchant by id."""

        return self._merchants.get(merchant_id)

    async def list_merchants(self) -> list[BusinessMerchant]:
        """Return all merchants for internal admin review."""

        return list(self._merchants.values())

    async def save_product(self, product: BusinessProduct) -> BusinessProduct:
        """Persist product metadata."""

        self._products[product.product_id] = product
        return product

    async def get_product(self, product_id: str) -> BusinessProduct | None:
        """Return one product by id."""

        return self._products.get(product_id)

    async def list_products(self, owner_id: str) -> list[BusinessProduct]:
        """Return products owned by one workspace owner."""

        return [product for product in self._products.values() if product.owner_id == owner_id]

    async def list_pending_products_for_review(self) -> list[BusinessProduct]:
        """Return products waiting for admin review."""

        return [product for product in self._products.values() if product.review_status == "pending"]

    async def save_product_image(self, image: BusinessProductImage) -> BusinessProductImage:
        """Persist product image metadata."""

        self._images[image.image_id] = image
        return image

    async def list_product_images(self, product_id: str) -> list[BusinessProductImage]:
        """Return product images for one product."""

        return [image for image in self._images.values() if image.product_id == product_id]

    async def save_offer(self, offer: BusinessProductOffer) -> BusinessProductOffer:
        """Persist product offer metadata."""

        self._offers[offer.offer_id] = offer
        return offer

    async def get_offer(self, product_id: str) -> BusinessProductOffer | None:
        """Return the sellable offer for one product."""

        return next((offer for offer in self._offers.values() if offer.product_id == product_id), None)

    async def save_import_job(self, job: CatalogImportJob) -> CatalogImportJob:
        """Persist catalog import job metadata."""

        self._import_jobs[job.import_id] = job
        return job

    async def get_import_job(self, import_id: str) -> CatalogImportJob | None:
        """Return one import job."""

        return self._import_jobs.get(import_id)

    async def save_import_errors(self, errors: list[CatalogImportRowError]) -> None:
        """Persist row-level import validation errors."""

        self._import_errors.extend(errors)

    async def list_import_errors(self, import_id: str) -> list[CatalogImportRowError]:
        """Return row-level errors for one import job."""

        return [error for error in self._import_errors if error.import_id == import_id]

    async def get_catalog_load_metrics(self, merchant: BusinessMerchant) -> dict[str, int]:
        """Return advisory workload metrics for tenant tier recommendations."""

        products = [product for product in self._products.values() if product.merchant_id == merchant.merchant_id]
        product_ids = {product.product_id for product in products}
        images = [image for image in self._images.values() if image.product_id in product_ids]
        imports = [job for job in self._import_jobs.values() if job.merchant_id == merchant.merchant_id]
        return {
            "product_count": len(products),
            "imports_last_30_days": len(imports),
            "largest_import_rows": max((job.total_rows for job in imports), default=0),
            "images_last_30_days": len(images),
            "failed_imports_last_30_days": sum(1 for job in imports if job.status is CatalogImportStatus.FAILED),
        }

    async def search_approved_matches(
        self,
        *,
        profile: SimilarityQueryProfile,
        limit: int,
    ) -> list[HydratedCatalogMatch]:
        """Return approved local catalog matches for similar-search fallback."""

        exact_matches = await self._search_approved_matches(profile=profile, limit=limit, require_exact_category=True)
        if exact_matches:
            return exact_matches
        return await self._search_approved_matches(profile=profile, limit=limit, require_exact_category=False)

    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]:
        """Return public-search-safe products for vector hit hydration."""

        records = await self.list_approved_search_records_by_product_ids(product_ids=product_ids)
        return [_product_record_from_search_record(record) for record in records]

    async def list_offers_for_products(
        self,
        product_ids: list[str],
        *,
        marketplace_filters: list[str],
    ) -> list[CatalogOfferRecord]:
        """Return public-search-safe offers for vector hit hydration."""

        records = await self.list_approved_search_records_by_product_ids(product_ids=product_ids)
        requested_marketplaces = set(marketplace_filters)
        offers = [_offer_record_from_search_record(record) for record in records]
        if requested_marketplaces:
            return [offer for offer in offers if offer.marketplace in requested_marketplaces]
        return offers

    async def list_approved_search_records(self, *, limit: int) -> list[BusinessCatalogSearchRecord]:
        """Return approved catalog projections for vector reindex jobs."""

        records: list[BusinessCatalogSearchRecord] = []
        for product in self._products.values():
            offer = await self.get_offer(product.product_id)
            record = project_business_product_for_search(product, offer)
            if record is None:
                continue
            records.append(record)
            if len(records) >= limit:
                break
        return records

    async def list_approved_search_records_by_product_ids(self, *, product_ids: list[str]) -> list[BusinessCatalogSearchRecord]:
        """Return approved catalog projections for specific product ids."""

        records: list[BusinessCatalogSearchRecord] = []
        for product_id in product_ids:
            product = self._products.get(product_id)
            if product is None:
                continue
            offer = await self.get_offer(product.product_id)
            record = project_business_product_for_search(product, offer)
            if record is not None:
                records.append(record)
        return records

    async def mark_search_indexed(self, *, product_ids: list[str]) -> None:
        """Mark products as successfully indexed for search."""

        indexed_at = utc_now()
        for product_id in product_ids:
            product = self._products.get(product_id)
            if product is None:
                continue
            self._products[product_id] = product.model_copy(
                update={
                    "search_index_status": SearchIndexStatus.INDEXED,
                    "search_index_error": None,
                    "search_indexed_at": indexed_at,
                    "updated_at": indexed_at,
                }
            )

    async def mark_search_index_failed(self, *, product_ids: list[str], reason: str) -> None:
        """Mark products as failed during search indexing."""

        failed_at = utc_now()
        safe_reason = reason.strip()[:1000] or "Search indexing failed."
        for product_id in product_ids:
            product = self._products.get(product_id)
            if product is None:
                continue
            self._products[product_id] = product.model_copy(
                update={
                    "search_index_status": SearchIndexStatus.FAILED,
                    "search_index_error": safe_reason,
                    "updated_at": failed_at,
                }
            )

    async def _search_approved_matches(
        self,
        *,
        profile: SimilarityQueryProfile,
        limit: int,
        require_exact_category: bool,
    ) -> list[HydratedCatalogMatch]:
        """Search approved local catalog records, optionally enforcing category."""

        matches: list[HydratedCatalogMatch] = []
        for product in self._products.values():
            if product.status is not BusinessProductStatus.ACTIVE:
                continue
            if product.review_status is not ReviewStatus.APPROVED:
                continue
            if require_exact_category and profile.category and product.category.lower() != profile.category.lower():
                continue
            offer = await self.get_offer(product.product_id)
            if offer is None or offer.availability is ProductAvailability.OUT_OF_STOCK:
                continue
            matches.append(_local_catalog_match(product=product, offer=offer, query_text=profile.embedding_input))
            if len(matches) >= limit:
                break
        return matches


def _local_catalog_match(
    *,
    product: BusinessProduct,
    offer: BusinessProductOffer,
    query_text: str,
) -> HydratedCatalogMatch:
    """Map one approved business catalog record into similar-search output shape."""

    return HydratedCatalogMatch(
        product=CatalogProductRecord(
            product_id=product.product_id,
            title=product.title,
            category=product.category,
            brand=product.source_type,
            color=_infer_color(query_text),
        ),
        offer=CatalogOfferRecord(
            offer_id=offer.offer_id,
            product_id=product.product_id,
            marketplace="local_catalog",
            price_amount=float(offer.price_amount),
            currency=offer.currency.upper(),
            product_url=str(offer.product_url) if offer.product_url is not None else f"local://business-catalog/{product.product_id}",
            is_available=offer.availability is ProductAvailability.IN_STOCK,
            country_code=product.country_code.upper(),
            city=product.city,
            delivery_regions=list(offer.delivery_regions),
            source_trust_score=0.85,
        ),
        similarity_score=_keyword_similarity(product=product, query_text=query_text),
    )


def _product_record_from_search_record(record: BusinessCatalogSearchRecord) -> CatalogProductRecord:
    """Map approved business catalog projection into generic search product shape."""

    return CatalogProductRecord(
        product_id=record.product_id,
        title=record.title,
        category=record.category,
        brand=record.source_type,
        color=None,
    )


def _offer_record_from_search_record(record: BusinessCatalogSearchRecord) -> CatalogOfferRecord:
    """Map approved business catalog projection into generic search offer shape."""

    product_url = str(record.product_url) if record.product_url is not None else f"local://business-catalog/{record.product_id}"
    return CatalogOfferRecord(
        offer_id=f"business_offer_{record.product_id}",
        product_id=record.product_id,
        marketplace=record.marketplace_source_type,
        price_amount=float(record.price_amount),
        currency=record.currency.upper(),
        product_url=product_url,
        is_available=record.availability is ProductAvailability.IN_STOCK,
        country_code=record.country_code.upper(),
        city=record.city,
        delivery_regions=list(record.delivery_regions),
        source_trust_score=record.source_trust_score,
    )


def _keyword_similarity(*, product: BusinessProduct, query_text: str) -> float:
    """Compute a conservative deterministic score for local fallback ranking."""

    haystack = f"{product.title} {product.category} {product.description or ''}".lower()
    tokens = [token for token in query_text.lower().replace(";", " ").replace(",", " ").split() if len(token) > 2]
    if not tokens:
        return 0.6
    matched = sum(1 for token in tokens if token in haystack)
    return min(0.88, 0.58 + (matched / len(tokens)) * 0.3)


def _infer_color(query_text: str) -> str | None:
    """Extract a simple color token from the backend garment profile text."""

    marker = "color:"
    lowered = query_text.lower()
    if marker not in lowered:
        return None
    value = lowered.split(marker, 1)[1].split(";", 1)[0].strip()
    return value or None
