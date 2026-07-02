from __future__ import annotations

from scripts import business_catalog_staging_smoke as smoke


def test_catalog_csv_contains_required_columns() -> None:
    content = smoke._catalog_csv().decode("utf-8")

    assert "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions" in content
    assert "Smoke shirt" in content


def test_multipart_request_uses_business_catalog_file_field(monkeypatch) -> None:
    captured = {}

    def _send(**kwargs):
        captured.update(kwargs)
        return smoke.SmokeResponse(status_code=200, body={"ok": True})

    monkeypatch.setattr(smoke, "_send", _send)

    response = smoke._multipart_request(
        base_url="https://api.example.test",
        path="/api/business/catalog-imports",
        timeout=1,
        fields=None,
        file_field="file",
        filename="products.csv",
        content_type="text/csv",
        content=b"csv",
        headers={"Idempotency-Key": "key-1"},
    )

    assert response.status_code == 200
    assert b'name="file"; filename="products.csv"' in captured["body"]
    assert captured["headers"]["Idempotency-Key"] == "key-1"
