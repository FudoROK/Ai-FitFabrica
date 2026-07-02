from __future__ import annotations

import pytest

from src.use_cases.business_catalog.import_parser import parse_business_catalog_csv


def test_business_catalog_import_parser_accepts_valid_csv_rows() -> None:
    result = parse_business_catalog_csv(
        """title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions
White shirt,shirt,14990,KZT,KZ,Almaty,in_stock,https://example.com/shirt,"Almaty;Astana"
"""
    )

    assert len(result.rows) == 1
    assert not result.errors
    assert result.rows[0].title == "White shirt"
    assert result.rows[0].delivery_regions == ["Almaty", "Astana"]


def test_business_catalog_import_parser_reports_missing_required_columns() -> None:
    result = parse_business_catalog_csv("title,category\nWhite shirt,shirt\n")

    assert not result.rows
    assert result.errors[0].safe_code == "missing_required_columns"
    assert "price_amount" in result.errors[0].message


def test_business_catalog_import_parser_reports_row_level_errors() -> None:
    result = parse_business_catalog_csv(
        """title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions
White shirt,shirt,-1,KZT,KZ,Almaty,in_stock,https://example.com/shirt,Almaty
Blue dress,dress,19990,KZT,KZ,Astana,in_stock,https://example.com/dress,Astana
Bad currency,shirt,100,US,KZ,Almaty,in_stock,https://example.com/bad,Almaty
Bad URL,shirt,100,KZT,KZ,Almaty,in_stock,not-a-url,Almaty
"""
    )

    assert len(result.rows) == 1
    assert result.rows[0].title == "Blue dress"
    assert [error.safe_code for error in result.errors] == [
        "invalid_price",
        "invalid_currency",
        "invalid_url",
    ]


def test_business_catalog_import_parser_rejects_empty_csv() -> None:
    result = parse_business_catalog_csv("")

    assert not result.rows
    assert result.errors[0].safe_code == "empty_csv"
