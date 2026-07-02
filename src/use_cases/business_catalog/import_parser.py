"""CSV parser for business catalog imports."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import StringIO
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from src.domain.business_catalog import ProductAvailability


REQUIRED_IMPORT_COLUMNS = frozenset(
    {
        "title",
        "category",
        "price_amount",
        "currency",
        "country_code",
        "city",
        "availability",
        "product_url",
        "delivery_regions",
    }
)


class BusinessCatalogImportRow(BaseModel):
    """Validated normalized product row from CSV import."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(ge=2)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price_amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1)
    availability: ProductAvailability
    product_url: str | None = None
    delivery_regions: list[str] = Field(default_factory=list)


class BusinessCatalogImportParseError(BaseModel):
    """Safe row-level parser error."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(ge=1)
    field_name: str
    safe_code: str
    message: str


@dataclass(frozen=True)
class BusinessCatalogImportParseResult:
    """Parser output with accepted rows and safe validation errors."""

    rows: list[BusinessCatalogImportRow]
    errors: list[BusinessCatalogImportParseError]


def parse_business_catalog_csv(content: str) -> BusinessCatalogImportParseResult:
    """Parse CSV catalog content into accepted rows and row-level errors."""

    if not content.strip():
        return BusinessCatalogImportParseResult(
            rows=[],
            errors=[
                BusinessCatalogImportParseError(
                    row_number=1,
                    field_name="file",
                    safe_code="empty_csv",
                    message="CSV file is empty.",
                )
            ],
        )

    reader = csv.DictReader(StringIO(content))
    fieldnames = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_IMPORT_COLUMNS - fieldnames)
    if missing:
        return BusinessCatalogImportParseResult(
            rows=[],
            errors=[
                BusinessCatalogImportParseError(
                    row_number=1,
                    field_name="header",
                    safe_code="missing_required_columns",
                    message=f"Missing required columns: {', '.join(missing)}.",
                )
            ],
        )

    rows: list[BusinessCatalogImportRow] = []
    errors: list[BusinessCatalogImportParseError] = []
    for row_number, raw_row in enumerate(reader, start=2):
        parsed, row_errors = _parse_row(row_number=row_number, raw_row=raw_row)
        if row_errors:
            errors.extend(row_errors)
            continue
        if parsed is not None:
            rows.append(parsed)
    return BusinessCatalogImportParseResult(rows=rows, errors=errors)


def _parse_row(
    *,
    row_number: int,
    raw_row: dict[str, str | None],
) -> tuple[BusinessCatalogImportRow | None, list[BusinessCatalogImportParseError]]:
    errors: list[BusinessCatalogImportParseError] = []
    title = _value(raw_row, "title")
    category = _value(raw_row, "category")
    country_code = _value(raw_row, "country_code").upper()
    city = _value(raw_row, "city")
    currency = _value(raw_row, "currency").upper()
    product_url = _value(raw_row, "product_url")
    delivery_regions = _split_regions(_value(raw_row, "delivery_regions"))

    for field_name, value in (("title", title), ("category", category), ("country_code", country_code), ("city", city)):
        if not value:
            errors.append(_error(row_number, field_name, "missing_value", f"{field_name} is required."))

    price_amount = _parse_price(row_number=row_number, value=_value(raw_row, "price_amount"), errors=errors)
    if len(currency) != 3:
        errors.append(_error(row_number, "currency", "invalid_currency", "Currency must be a 3-letter code."))
    availability = _parse_availability(row_number=row_number, value=_value(raw_row, "availability"), errors=errors)
    if product_url and not _is_valid_url(product_url):
        errors.append(_error(row_number, "product_url", "invalid_url", "Product URL must be an absolute URL."))

    if errors or price_amount is None or availability is None:
        return None, errors
    return (
        BusinessCatalogImportRow(
            row_number=row_number,
            title=title,
            category=category,
            price_amount=price_amount,
            currency=currency,
            country_code=country_code,
            city=city,
            availability=availability,
            product_url=product_url or None,
            delivery_regions=delivery_regions,
        ),
        [],
    )


def _value(raw_row: dict[str, str | None], field_name: str) -> str:
    return (raw_row.get(field_name) or "").strip()


def _split_regions(value: str) -> list[str]:
    return [region.strip() for region in value.split(";") if region.strip()]


def _parse_price(
    *,
    row_number: int,
    value: str,
    errors: list[BusinessCatalogImportParseError],
) -> Decimal | None:
    try:
        price = Decimal(value)
    except (InvalidOperation, ValueError):
        errors.append(_error(row_number, "price_amount", "invalid_price", "Price must be a non-negative number."))
        return None
    if price < Decimal("0"):
        errors.append(_error(row_number, "price_amount", "invalid_price", "Price must be a non-negative number."))
        return None
    return price


def _parse_availability(
    *,
    row_number: int,
    value: str,
    errors: list[BusinessCatalogImportParseError],
) -> ProductAvailability | None:
    try:
        return ProductAvailability(value)
    except ValueError:
        errors.append(_error(row_number, "availability", "invalid_availability", "Availability is not supported."))
        return None


def _is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _error(row_number: int, field_name: str, safe_code: str, message: str) -> BusinessCatalogImportParseError:
    return BusinessCatalogImportParseError(
        row_number=row_number,
        field_name=field_name,
        safe_code=safe_code,
        message=message,
    )
