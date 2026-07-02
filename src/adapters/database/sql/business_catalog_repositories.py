"""SQL-backed repository for seller-owned business catalog persistence."""

from __future__ import annotations

from sqlalchemy import func, select, update

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductOffer,
    CatalogImportJob,
    CatalogImportRowError,
    ProductAvailability,
    SearchIndexStatus,
    utc_now,
)
from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord, HydratedCatalogMatch, SimilarityQueryProfile
from src.use_cases.business_catalog.search_projection import BusinessCatalogSearchRecord, project_business_product_for_search

from .business_catalog_models import (
    BusinessCatalogImportJobRow,
    BusinessCatalogImportRowErrorRow,
    BusinessMerchantRow,
    BusinessProductImageRow,
    BusinessProductOfferRow,
    BusinessProductRow,
)
from .business_catalog_serialization import (
    image_from_row,
    image_to_row,
    import_error_from_row,
    import_error_to_row,
    import_job_from_row,
    import_job_to_row,
    merchant_from_row,
    merchant_to_row,
    offer_from_row,
    offer_to_row,
    product_from_row,
    product_to_row,
)


class SqlBusinessCatalogRepository:
    """Persist B2B product catalog state in portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""

        self._session_factory = session_factory

    async def save_merchant(self, merchant: BusinessMerchant) -> BusinessMerchant:
        """Persist a merchant profile."""

        async with self._session_factory() as session:
            await session.merge(merchant_to_row(merchant))
            await session.commit()
        return merchant

    async def get_merchant_by_owner(self, owner_id: str) -> BusinessMerchant | None:
        """Return the merchant profile owned by one workspace owner."""

        async with self._session_factory() as session:
            row = (
                await session.scalars(
                    select(BusinessMerchantRow).where(BusinessMerchantRow.owner_id == owner_id)
                )
            ).first()
            return None if row is None else merchant_from_row(row)

    async def get_merchant(self, merchant_id: str) -> BusinessMerchant | None:
        """Return one merchant profile by id."""

        async with self._session_factory() as session:
            row = await session.get(BusinessMerchantRow, merchant_id)
            return None if row is None else merchant_from_row(row)

    async def list_merchants(self) -> list[BusinessMerchant]:
        """Return all business merchants for internal admin review."""

        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(BusinessMerchantRow).order_by(BusinessMerchantRow.updated_at.desc(), BusinessMerchantRow.merchant_id.asc())
                )
            ).all()
            return [merchant_from_row(row) for row in rows]

    async def save_product(self, product: BusinessProduct) -> BusinessProduct:
        """Persist product metadata."""

        async with self._session_factory() as session:
            await session.merge(product_to_row(product))
            await session.commit()
        return product

    async def get_product(self, product_id: str) -> BusinessProduct | None:
        """Return one product by id."""

        async with self._session_factory() as session:
            row = await session.get(BusinessProductRow, product_id)
            return None if row is None else product_from_row(row)

    async def list_products(self, owner_id: str) -> list[BusinessProduct]:
        """Return products owned by one workspace owner."""

        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(BusinessProductRow)
                    .where(BusinessProductRow.owner_id == owner_id)
                    .order_by(BusinessProductRow.updated_at.desc(), BusinessProductRow.product_id.asc())
                )
            ).all()
            return [product_from_row(row) for row in rows]

    async def list_pending_products_for_review(self) -> list[BusinessProduct]:
        """Return products waiting for admin catalog review."""

        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(BusinessProductRow)
                    .where(BusinessProductRow.review_status == "pending")
                    .order_by(BusinessProductRow.updated_at.asc(), BusinessProductRow.product_id.asc())
                )
            ).all()
            return [product_from_row(row) for row in rows]

    async def save_product_image(self, image: BusinessProductImage) -> BusinessProductImage:
        """Persist product image metadata."""

        async with self._session_factory() as session:
            await session.merge(image_to_row(image))
            await session.commit()
        return image

    async def list_product_images(self, product_id: str) -> list[BusinessProductImage]:
        """Return images attached to one product."""

        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(BusinessProductImageRow)
                    .where(BusinessProductImageRow.product_id == product_id)
                    .order_by(BusinessProductImageRow.sort_order.asc(), BusinessProductImageRow.image_id.asc())
                )
            ).all()
            return [image_from_row(row) for row in rows]

    async def save_offer(self, offer: BusinessProductOffer) -> BusinessProductOffer:
        """Persist product offer metadata."""

        async with self._session_factory() as session:
            await session.merge(offer_to_row(offer))
            await session.commit()
        return offer

    async def get_offer(self, product_id: str) -> BusinessProductOffer | None:
        """Return sellable offer for one product, if present."""

        async with self._session_factory() as session:
            row = (
                await session.scalars(
                    select(BusinessProductOfferRow).where(BusinessProductOfferRow.product_id == product_id)
                )
            ).first()
            return None if row is None else offer_from_row(row)

    async def save_import_job(self, job: CatalogImportJob) -> CatalogImportJob:
        """Persist catalog import job metadata."""

        async with self._session_factory() as session:
            await session.merge(import_job_to_row(job))
            await session.commit()
        return job

    async def get_import_job(self, import_id: str) -> CatalogImportJob | None:
        """Return one catalog import job by id."""

        async with self._session_factory() as session:
            row = await session.get(BusinessCatalogImportJobRow, import_id)
            return None if row is None else import_job_from_row(row)

    async def save_import_errors(self, errors: list[CatalogImportRowError]) -> None:
        """Persist row-level import validation errors."""

        async with self._session_factory() as session:
            session.add_all(import_error_to_row(error) for error in errors)
            await session.commit()

    async def list_import_errors(self, import_id: str) -> list[CatalogImportRowError]:
        """Return row-level validation errors for one import job."""

        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(BusinessCatalogImportRowErrorRow)
                    .where(BusinessCatalogImportRowErrorRow.import_id == import_id)
                    .order_by(BusinessCatalogImportRowErrorRow.row_number.asc(), BusinessCatalogImportRowErrorRow.id.asc())
                )
            ).all()
            return [import_error_from_row(row) for row in rows]

    async def get_catalog_load_metrics(self, merchant: BusinessMerchant) -> dict[str, int]:
        """Return lightweight admin workload metrics for tier recommendations."""

        async with self._session_factory() as session:
            product_count = await session.scalar(
                select(func.count()).select_from(BusinessProductRow).where(BusinessProductRow.merchant_id == merchant.merchant_id)
            )
            image_count = await session.scalar(
                select(func.count())
                .select_from(BusinessProductImageRow)
                .join(BusinessProductRow, BusinessProductRow.product_id == BusinessProductImageRow.product_id)
                .where(BusinessProductRow.merchant_id == merchant.merchant_id)
            )
            import_count = await session.scalar(
                select(func.count())
                .select_from(BusinessCatalogImportJobRow)
                .where(BusinessCatalogImportJobRow.merchant_id == merchant.merchant_id)
            )
            largest_import_rows = await session.scalar(
                select(func.max(BusinessCatalogImportJobRow.total_rows)).where(
                    BusinessCatalogImportJobRow.merchant_id == merchant.merchant_id
                )
            )
            failed_import_count = await session.scalar(
                select(func.count())
                .select_from(BusinessCatalogImportJobRow)
                .where(
                    BusinessCatalogImportJobRow.merchant_id == merchant.merchant_id,
                    BusinessCatalogImportJobRow.status == "failed",
                )
            )
            return {
                "product_count": int(product_count or 0),
                "imports_last_30_days": int(import_count or 0),
                "largest_import_rows": int(largest_import_rows or 0),
                "images_last_30_days": int(image_count or 0),
                "failed_imports_last_30_days": int(failed_import_count or 0),
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

        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(BusinessProductRow, BusinessProductOfferRow)
                    .join(BusinessProductOfferRow, BusinessProductOfferRow.product_id == BusinessProductRow.product_id)
                    .where(
                        BusinessProductRow.status == "active",
                        BusinessProductRow.review_status == "approved",
                        BusinessProductOfferRow.availability != "out_of_stock",
                    )
                    .order_by(BusinessProductRow.updated_at.desc(), BusinessProductRow.product_id.asc())
                    .limit(limit)
                )
            ).all()
        records: list[BusinessCatalogSearchRecord] = []
        for product_row, offer_row in rows:
            record = project_business_product_for_search(product_from_row(product_row), offer_from_row(offer_row))
            if record is not None:
                records.append(record)
        return records

    async def list_approved_search_records_by_product_ids(self, *, product_ids: list[str]) -> list[BusinessCatalogSearchRecord]:
        """Return approved catalog projections for specific product ids."""

        if not product_ids:
            return []
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(BusinessProductRow, BusinessProductOfferRow)
                    .join(BusinessProductOfferRow, BusinessProductOfferRow.product_id == BusinessProductRow.product_id)
                    .where(
                        BusinessProductRow.product_id.in_(product_ids),
                        BusinessProductRow.status == "active",
                        BusinessProductRow.review_status == "approved",
                        BusinessProductOfferRow.availability != "out_of_stock",
                    )
                    .order_by(BusinessProductRow.product_id.asc())
                )
            ).all()
        records: list[BusinessCatalogSearchRecord] = []
        for product_row, offer_row in rows:
            record = project_business_product_for_search(product_from_row(product_row), offer_from_row(offer_row))
            if record is not None:
                records.append(record)
        return records

    async def mark_search_indexed(self, *, product_ids: list[str]) -> None:
        """Mark approved products as successfully indexed for search."""

        if not product_ids:
            return
        indexed_at = utc_now()
        async with self._session_factory() as session:
            await session.execute(
                update(BusinessProductRow)
                .where(BusinessProductRow.product_id.in_(product_ids))
                .values(
                    search_index_status=SearchIndexStatus.INDEXED.value,
                    search_index_error=None,
                    search_indexed_at=indexed_at,
                    updated_at=indexed_at,
                )
            )
            await session.commit()

    async def mark_search_index_failed(self, *, product_ids: list[str], reason: str) -> None:
        """Mark approved products as failed during search indexing."""

        if not product_ids:
            return
        failed_at = utc_now()
        safe_reason = reason.strip()[:1000] or "Search indexing failed."
        async with self._session_factory() as session:
            await session.execute(
                update(BusinessProductRow)
                .where(BusinessProductRow.product_id.in_(product_ids))
                .values(
                    search_index_status=SearchIndexStatus.FAILED.value,
                    search_index_error=safe_reason,
                    updated_at=failed_at,
                )
            )
            await session.commit()

    async def _search_approved_matches(
        self,
        *,
        profile: SimilarityQueryProfile,
        limit: int,
        require_exact_category: bool,
    ) -> list[HydratedCatalogMatch]:
        """Search approved local catalog records, optionally enforcing category."""

        async with self._session_factory() as session:
            query = (
                select(BusinessProductRow, BusinessProductOfferRow)
                .join(BusinessProductOfferRow, BusinessProductOfferRow.product_id == BusinessProductRow.product_id)
                .where(
                    BusinessProductRow.status == "active",
                    BusinessProductRow.review_status == "approved",
                    BusinessProductOfferRow.availability != "out_of_stock",
                )
                .order_by(BusinessProductRow.updated_at.desc(), BusinessProductRow.product_id.asc())
                .limit(limit)
            )
            if require_exact_category and profile.category:
                query = query.where(func.lower(BusinessProductRow.category) == profile.category.lower())
            rows = (await session.execute(query)).all()
            matches: list[HydratedCatalogMatch] = []
            for product_row, offer_row in rows:
                product = product_from_row(product_row)
                offer = offer_from_row(offer_row)
                matches.append(_local_catalog_match(product=product, offer=offer, query_text=profile.embedding_input))
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
