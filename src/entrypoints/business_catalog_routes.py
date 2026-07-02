"""Business-facing API routes for seller-owned product catalog state."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.domain.business_catalog import BusinessMerchant, BusinessProduct, BusinessProductImage, ProductAvailability, ProductImageRole
from src.domain.business_catalog import CatalogImportJob, CatalogImportRowError
from src.entrypoints.runtime_dependencies import business_catalog_service, portable_infrastructure
from src.settings import Settings
from src.use_cases.business_catalog.service import (
    BusinessCatalogForbiddenError,
    BusinessCatalogNotFoundError,
    BusinessCatalogOperationError,
    BusinessCatalogBackpressureError,
    BusinessCatalogValidationError,
    CreateProductRequest,
    ProductOfferInput,
    UploadProductImageRequest,
    UpsertMerchantRequest,
)

router = APIRouter(prefix="/api/business", tags=["business-catalog"])


class BusinessMerchantPayload(BaseModel):
    """Typed payload for business merchant persistence."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    contact_email: str | None = Field(default=None, max_length=255)
    instagram_url: HttpUrl | None = None
    website_url: HttpUrl | None = None


class BusinessMerchantResponse(BaseModel):
    """Business merchant response envelope."""

    model_config = ConfigDict(extra="forbid")

    merchant: BusinessMerchant


class BusinessProductOfferPayload(BaseModel):
    """Typed payload for product offer input."""

    model_config = ConfigDict(extra="forbid")

    price_amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    availability: ProductAvailability
    product_url: HttpUrl | None = None
    delivery_regions: list[str] = Field(default_factory=list)


class BusinessProductPayload(BaseModel):
    """Typed payload for creating one business product."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    offer: BusinessProductOfferPayload
    source_type: str = Field(default="manual", min_length=1, max_length=64)


class BusinessProductResponse(BaseModel):
    """Business product response envelope."""

    model_config = ConfigDict(extra="forbid")

    product: BusinessProduct


class BusinessProductListResponse(BaseModel):
    """Business product list response envelope."""

    model_config = ConfigDict(extra="forbid")

    products: list[BusinessProduct]


class BusinessProductImageResponse(BaseModel):
    """Business product image response envelope."""

    model_config = ConfigDict(extra="forbid")

    image: BusinessProductImage


class BusinessCatalogImportResponse(BaseModel):
    """Business catalog import response envelope."""

    model_config = ConfigDict(extra="forbid")

    import_job: CatalogImportJob
    errors: list[CatalogImportRowError] = Field(default_factory=list)


class BusinessCatalogImportJobResponse(BaseModel):
    """Business catalog import job response envelope."""

    model_config = ConfigDict(extra="forbid")

    import_job: CatalogImportJob


class BusinessCatalogImportErrorsResponse(BaseModel):
    """Business catalog import row errors response envelope."""

    model_config = ConfigDict(extra="forbid")

    errors: list[CatalogImportRowError]


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""

    return request.app.state.settings


def _owner_id(settings: Settings) -> str:
    """Resolve current business workspace owner id with existing sandbox fallback."""

    return getattr(settings, "default_person_credit_account_id", "public-person")


def _service_or_error(settings: Settings):
    service = business_catalog_service(settings)
    if service is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "business_catalog_storage_unavailable",
                    "message": "Business catalog storage is not configured.",
                }
            },
        )
    return service


def _error_response(exc: BusinessCatalogNotFoundError | BusinessCatalogForbiddenError | BusinessCatalogValidationError) -> JSONResponse:
    """Map business catalog use-case errors to structured API errors."""

    if isinstance(exc, BusinessCatalogNotFoundError):
        return JSONResponse(status_code=404, content={"error": {"code": "business_catalog_not_found", "message": str(exc)}})
    if isinstance(exc, BusinessCatalogForbiddenError):
        return JSONResponse(status_code=403, content={"error": {"code": "business_catalog_forbidden", "message": str(exc)}})
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "business_catalog_validation_failed", "message": str(exc)}},
    )


def _operation_error_response(exc: BusinessCatalogOperationError) -> JSONResponse:
    """Map catalog infrastructure failures to structured retry-safe API errors."""

    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": exc.safe_code,
                "message": str(exc),
                "details": {
                    "cleanup_required": exc.cleanup_required,
                    "cleanup_object_key": exc.cleanup_object_key,
                },
            }
        },
    )


def _backpressure_error_response(exc: BusinessCatalogBackpressureError) -> JSONResponse:
    """Map catalog workload limit failures to structured backpressure errors."""

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": exc.safe_code,
                "message": str(exc),
                "details": {
                    "limit_name": exc.limit_name,
                    "limit_value": exc.limit_value,
                    "actual_value": exc.actual_value,
                },
            }
        },
    )


@router.get("/merchant", response_model=BusinessMerchantResponse)
async def get_business_merchant(
    settings: Annotated[Settings, Depends(_settings)],
) -> BusinessMerchantResponse | JSONResponse:
    """Return the current owner's business merchant profile."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    merchant = await service.get_merchant(_owner_id(settings))
    if merchant is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "business_catalog_not_found", "message": "Business merchant was not found."}},
        )
    return BusinessMerchantResponse(merchant=merchant)


@router.post("/merchant", response_model=BusinessMerchantResponse)
async def save_business_merchant(
    payload: BusinessMerchantPayload,
    settings: Annotated[Settings, Depends(_settings)],
) -> BusinessMerchantResponse | JSONResponse:
    """Create or update the current owner's business merchant profile."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    merchant = await service.upsert_merchant(
        _owner_id(settings),
        UpsertMerchantRequest(**payload.model_dump()),
    )
    return BusinessMerchantResponse(merchant=merchant)


@router.get("/products", response_model=BusinessProductListResponse)
async def list_business_products(
    settings: Annotated[Settings, Depends(_settings)],
) -> BusinessProductListResponse | JSONResponse:
    """List products owned by the current business workspace."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    return BusinessProductListResponse(products=await service.list_products(_owner_id(settings)))


@router.get("/products/{product_id}/images/primary", response_model=None)
async def get_public_business_product_primary_image(
    product_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the primary image for an active approved catalog product."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        image = await service.get_public_primary_product_image(product_id)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    if image is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "business_catalog_image_not_found", "message": "Primary product image was not found."}},
        )
    try:
        payload = portable_infrastructure(settings).object_storage.get_bytes(image.object_key)
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "business_catalog_image_unavailable", "message": "Primary product image is unavailable."}},
        )
    return Response(content=payload, media_type=image.content_type)


@router.post("/products", response_model=BusinessProductResponse)
async def create_business_product(
    payload: BusinessProductPayload,
    settings: Annotated[Settings, Depends(_settings)],
) -> BusinessProductResponse | JSONResponse:
    """Create one draft business catalog product."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.create_product(
            _owner_id(settings),
            CreateProductRequest(
                title=payload.title,
                category=payload.category,
                description=payload.description,
                country_code=payload.country_code,
                city=payload.city,
                source_type=payload.source_type,
                offer=ProductOfferInput(**payload.offer.model_dump()),
            ),
        )
    except BusinessCatalogBackpressureError as exc:
        return _backpressure_error_response(exc)
    except BusinessCatalogOperationError as exc:
        return _operation_error_response(exc)
    except BusinessCatalogBackpressureError as exc:
        return _backpressure_error_response(exc)
    except BusinessCatalogOperationError as exc:
        return _operation_error_response(exc)
    except BusinessCatalogBackpressureError as exc:
        return _backpressure_error_response(exc)
    except BusinessCatalogOperationError as exc:
        return _operation_error_response(exc)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return BusinessProductResponse(product=product)


@router.post("/products/{product_id}/images", response_model=BusinessProductImageResponse)
async def upload_business_product_image(
    product_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    file: Annotated[UploadFile, File()],
    role: Annotated[ProductImageRole, Form()] = ProductImageRole.PRIMARY,
    sort_order: Annotated[int, Form(ge=0)] = 0,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> BusinessProductImageResponse | JSONResponse:
    """Upload and attach one product image through backend-owned storage."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    content = await file.read()
    try:
        image = await service.upload_product_image(
            _owner_id(settings),
            UploadProductImageRequest(
                product_id=product_id,
                filename=file.filename or "product-image",
                content_type=file.content_type or "application/octet-stream",
                content=content,
                role=role,
                sort_order=sort_order,
            ),
            idempotency_key=idempotency_key,
        )
    except BusinessCatalogBackpressureError as exc:
        return _backpressure_error_response(exc)
    except BusinessCatalogOperationError as exc:
        return _operation_error_response(exc)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return BusinessProductImageResponse(image=image)


@router.post("/catalog-imports", response_model=BusinessCatalogImportResponse)
async def create_business_catalog_import(
    settings: Annotated[Settings, Depends(_settings)],
    file: Annotated[UploadFile, File()],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> BusinessCatalogImportResponse | JSONResponse:
    """Import business catalog products from a CSV file."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    if file.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "business_catalog_validation_failed",
                    "message": "Only CSV catalog imports are currently supported.",
                }
            },
        )
    raw_content = await file.read()
    try:
        content = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "business_catalog_validation_failed", "message": "CSV file must be UTF-8 encoded."}},
        )
    try:
        import_job, errors = await service.import_products_from_csv(
            _owner_id(settings),
            file.filename or "products.csv",
            content,
            idempotency_key=idempotency_key,
        )
    except BusinessCatalogBackpressureError as exc:
        return _backpressure_error_response(exc)
    except BusinessCatalogOperationError as exc:
        return _operation_error_response(exc)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return BusinessCatalogImportResponse(import_job=import_job, errors=errors)


@router.get("/catalog-imports/{import_id}", response_model=BusinessCatalogImportJobResponse)
async def get_business_catalog_import(
    import_id: str,
    settings: Annotated[Settings, Depends(_settings)],
) -> BusinessCatalogImportJobResponse | JSONResponse:
    """Return one catalog import job for the current owner."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        import_job = await service.get_import_job(_owner_id(settings), import_id)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    if import_job is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "business_catalog_not_found", "message": "Catalog import was not found."}},
        )
    return BusinessCatalogImportJobResponse(import_job=import_job)


@router.get("/catalog-imports/{import_id}/errors", response_model=BusinessCatalogImportErrorsResponse)
async def list_business_catalog_import_errors(
    import_id: str,
    settings: Annotated[Settings, Depends(_settings)],
) -> BusinessCatalogImportErrorsResponse | JSONResponse:
    """Return row-level errors for one catalog import job."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        errors = await service.list_import_errors(_owner_id(settings), import_id)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return BusinessCatalogImportErrorsResponse(errors=errors)


@router.post("/products/{product_id}/submit", response_model=BusinessProductResponse)
async def submit_business_product(
    product_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> BusinessProductResponse | JSONResponse:
    """Submit one business product for admin review."""

    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.submit_product(_owner_id(settings), product_id, idempotency_key=idempotency_key)
    except BusinessCatalogValidationError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "business_catalog_submit_blocked", "message": str(exc)}},
        )
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError) as exc:
        return _error_response(exc)
    return BusinessProductResponse(product=product)
