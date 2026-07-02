"""Mapping helpers between business catalog SQL rows and domain models."""

from __future__ import annotations

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductOffer,
    CatalogImportJob,
    CatalogImportRowError,
)

from .business_catalog_models import (
    BusinessCatalogImportJobRow,
    BusinessCatalogImportRowErrorRow,
    BusinessMerchantRow,
    BusinessProductImageRow,
    BusinessProductOfferRow,
    BusinessProductRow,
)


def merchant_to_row(model: BusinessMerchant) -> BusinessMerchantRow:
    """Convert a merchant domain model into a SQL row."""

    return BusinessMerchantRow(
        merchant_id=model.merchant_id,
        owner_id=model.owner_id,
        display_name=model.display_name,
        legal_name=model.legal_name,
        country_code=model.country_code,
        city=model.city,
        contact_email=model.contact_email,
        instagram_url=str(model.instagram_url) if model.instagram_url else None,
        website_url=str(model.website_url) if model.website_url else None,
        status=model.status.value,
        assigned_tier=model.assigned_tier,
        tier_assigned_reason=model.tier_assigned_reason,
        tier_assigned_by=model.tier_assigned_by,
        tier_assigned_at=model.tier_assigned_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def merchant_from_row(row: BusinessMerchantRow) -> BusinessMerchant:
    """Convert a merchant SQL row into a domain model."""

    return BusinessMerchant(
        merchant_id=row.merchant_id,
        owner_id=row.owner_id,
        display_name=row.display_name,
        legal_name=row.legal_name,
        country_code=row.country_code,
        city=row.city,
        contact_email=row.contact_email,
        instagram_url=row.instagram_url,
        website_url=row.website_url,
        status=row.status,
        assigned_tier=row.assigned_tier,
        tier_assigned_reason=row.tier_assigned_reason,
        tier_assigned_by=row.tier_assigned_by,
        tier_assigned_at=row.tier_assigned_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def product_to_row(model: BusinessProduct) -> BusinessProductRow:
    """Convert a product domain model into a SQL row."""

    return BusinessProductRow(
        product_id=model.product_id,
        merchant_id=model.merchant_id,
        owner_id=model.owner_id,
        title=model.title,
        category=model.category,
        description=model.description,
        country_code=model.country_code,
        city=model.city,
        status=model.status.value,
        review_status=model.review_status.value,
        source_type=model.source_type,
        review_reason=model.review_reason,
        category_validation_status=model.category_validation_status.value,
        category_validation_reason=model.category_validation_reason,
        visual_category=model.visual_category,
        visual_category_confidence=model.visual_category_confidence,
        category_validated_at=model.category_validated_at,
        search_index_status=model.search_index_status.value,
        search_index_error=model.search_index_error,
        search_indexed_at=model.search_indexed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def product_from_row(row: BusinessProductRow) -> BusinessProduct:
    """Convert a product SQL row into a domain model."""

    return BusinessProduct(
        product_id=row.product_id,
        merchant_id=row.merchant_id,
        owner_id=row.owner_id,
        title=row.title,
        category=row.category,
        description=row.description,
        country_code=row.country_code,
        city=row.city,
        status=row.status,
        review_status=row.review_status,
        source_type=row.source_type,
        review_reason=row.review_reason,
        category_validation_status=row.category_validation_status,
        category_validation_reason=row.category_validation_reason,
        visual_category=row.visual_category,
        visual_category_confidence=row.visual_category_confidence,
        category_validated_at=row.category_validated_at,
        search_index_status=row.search_index_status,
        search_index_error=row.search_index_error,
        search_indexed_at=row.search_indexed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def image_to_row(model: BusinessProductImage) -> BusinessProductImageRow:
    """Convert a product image domain model into a SQL row."""

    return BusinessProductImageRow(
        image_id=model.image_id,
        product_id=model.product_id,
        object_key=model.object_key,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        sha256=model.sha256,
        role=model.role.value,
        sort_order=model.sort_order,
        created_at=model.created_at,
    )


def image_from_row(row: BusinessProductImageRow) -> BusinessProductImage:
    """Convert a product image SQL row into a domain model."""

    return BusinessProductImage(
        image_id=row.image_id,
        product_id=row.product_id,
        object_key=row.object_key,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        sha256=row.sha256,
        role=row.role,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def offer_to_row(model: BusinessProductOffer) -> BusinessProductOfferRow:
    """Convert a product offer domain model into a SQL row."""

    return BusinessProductOfferRow(
        offer_id=model.offer_id,
        product_id=model.product_id,
        price_amount=model.price_amount,
        currency=model.currency,
        availability=model.availability.value,
        product_url=str(model.product_url) if model.product_url else None,
        delivery_regions_json=list(model.delivery_regions),
        updated_at=model.updated_at,
    )


def offer_from_row(row: BusinessProductOfferRow) -> BusinessProductOffer:
    """Convert a product offer SQL row into a domain model."""

    return BusinessProductOffer(
        offer_id=row.offer_id,
        product_id=row.product_id,
        price_amount=row.price_amount,
        currency=row.currency,
        availability=row.availability,
        product_url=row.product_url,
        delivery_regions=list(row.delivery_regions_json),
        updated_at=row.updated_at,
    )


def import_job_to_row(model: CatalogImportJob) -> BusinessCatalogImportJobRow:
    """Convert an import job domain model into a SQL row."""

    return BusinessCatalogImportJobRow(
        import_id=model.import_id,
        merchant_id=model.merchant_id,
        owner_id=model.owner_id,
        filename=model.filename,
        status=model.status.value,
        total_rows=model.total_rows,
        accepted_rows=model.accepted_rows,
        rejected_rows=model.rejected_rows,
        error_summary=model.error_summary,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )


def import_job_from_row(row: BusinessCatalogImportJobRow) -> CatalogImportJob:
    """Convert an import job SQL row into a domain model."""

    return CatalogImportJob(
        import_id=row.import_id,
        merchant_id=row.merchant_id,
        owner_id=row.owner_id,
        filename=row.filename,
        status=row.status,
        total_rows=row.total_rows,
        accepted_rows=row.accepted_rows,
        rejected_rows=row.rejected_rows,
        error_summary=row.error_summary,
        created_at=row.created_at,
        completed_at=row.completed_at,
    )


def import_error_to_row(model: CatalogImportRowError) -> BusinessCatalogImportRowErrorRow:
    """Convert an import row error domain model into a SQL row."""

    return BusinessCatalogImportRowErrorRow(
        import_id=model.import_id,
        row_number=model.row_number,
        field_name=model.field_name,
        safe_code=model.safe_code,
        message=model.message,
    )


def import_error_from_row(row: BusinessCatalogImportRowErrorRow) -> CatalogImportRowError:
    """Convert an import row error SQL row into a domain model."""

    return CatalogImportRowError(
        import_id=row.import_id,
        row_number=row.row_number,
        field_name=row.field_name,
        safe_code=row.safe_code,
        message=row.message,
    )
