from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts import load_realistic_business_catalog_staging as loader


def test_validation_summary_tracks_matched_and_blocked_products(monkeypatch) -> None:
    responses = [
        loader.HttpResponse(
            status_code=200,
            body={
                "result": {
                    "processed_count": 2,
                    "validated_count": 2,
                    "failed_count": 0,
                    "items": [
                        {
                            "product_id": "product_matched",
                            "status": "validated",
                            "product": {"category_validation_status": "matched"},
                        },
                        {
                            "product_id": "product_blocked",
                            "status": "validated",
                            "product": {"category_validation_status": "mismatch"},
                        },
                    ],
                }
            },
        )
    ]

    monkeypatch.setattr(loader, "_json_request", lambda *args, **kwargs: responses.pop(0))

    summary = loader._validate_pending_categories(
        args=SimpleNamespace(base_url="https://api.example.test", timeout=1),
        headers={"Authorization": "Bearer token"},
        expected_product_count=2,
    )

    assert summary.matched_product_ids == ["product_matched"]
    assert summary.blocked_product_ids == ["product_blocked"]


def test_approve_pending_requires_explicit_allow_for_category_blocks(monkeypatch) -> None:
    monkeypatch.setattr(loader, "_admin_headers", lambda args: {"Authorization": "Bearer token"})
    monkeypatch.setattr(
        loader,
        "_json_request",
        lambda *args, **kwargs: loader.HttpResponse(status_code=200, body={"products": []}),
    )
    monkeypatch.setattr(
        loader,
        "_validate_pending_categories",
        lambda **kwargs: loader.CategoryValidationSummary(
            processed_count=2,
            matched_product_ids=["product_matched"],
            blocked_product_ids=["product_blocked"],
        ),
    )

    with pytest.raises(RuntimeError, match="Category validation blocked 1 products"):
        loader._approve_pending(
            args=SimpleNamespace(
                base_url="https://api.example.test",
                timeout=1,
                allow_category_blocks=False,
            ),
            expected_product_count=2,
        )


def test_approve_pending_allows_blocked_products_when_flagged(monkeypatch) -> None:
    monkeypatch.setattr(loader, "_admin_headers", lambda args: {"Authorization": "Bearer token"})
    monkeypatch.setattr(
        loader,
        "_json_request",
        lambda *args, **kwargs: loader.HttpResponse(status_code=200, body={"products": []}),
    )
    monkeypatch.setattr(
        loader,
        "_validate_pending_categories",
        lambda **kwargs: loader.CategoryValidationSummary(
            processed_count=2,
            matched_product_ids=["product_matched"],
            blocked_product_ids=["product_blocked"],
        ),
    )
    monkeypatch.setattr(loader, "_approve_matched_pending", lambda **kwargs: ["product_matched"])

    summary = loader._approve_pending(
        args=SimpleNamespace(
            base_url="https://api.example.test",
            timeout=1,
            allow_category_blocks=True,
        ),
        expected_product_count=2,
    )

    assert summary.approved_product_ids == ["product_matched"]
    assert summary.blocked_product_ids == ["product_blocked"]


def test_validate_pack_rejects_category_mismatch_between_csv_and_image_name(tmp_path) -> None:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    image_path = image_dir / "001_blue_denim_midi_skirt.png"
    image_path.write_bytes(b"image")

    rows = [{"title": "Blue denim skirt", "category": "dress"}]
    manifest = {"Blue denim skirt": {"image_filename": image_path.name}}

    with pytest.raises(RuntimeError, match="Category mismatch"):
        loader._validate_pack(rows=rows, manifest=manifest, image_dir=image_dir)


def test_expected_category_from_image_name_does_not_confuse_pocket_shirt_with_tshirt() -> None:
    assert loader._expected_category_from_image_name("004_ivory_pocket_shirt.png") == "shirt"
