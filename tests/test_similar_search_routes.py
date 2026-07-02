from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app
from src.use_cases.product_card.garment_identity_errors import GarmentIdentityAnalysisFailure

client = TestClient(app)


class _ServiceStub:
    def __init__(self) -> None:
        self.last_request = None

    async def search(self, request):
        self.last_request = request
        return {
            "results": [
                {
                    "product_id": "product-1",
                    "title": "Black midi dress",
                    "similarity_score": 0.91,
                    "price_amount": 99.0,
                    "currency": "USD",
                    "marketplace": "lamoda",
                    "is_cheaper_alternative": True,
                    "explanation": "Similarity 0.91, fits budget, cheaper than reference.",
                    "location_match": "unknown",
                    "country_code": "KZ",
                    "city": "Almaty",
                    "delivery_regions": ["Almaty"],
                    "image_url": "/api/business/products/product-1/images/primary",
                    "offer_url": "https://seller.example/products/product-1",
                }
            ]
        }


class _ObjectStorageStub:
    def __init__(self) -> None:
        self.objects = {}

    def put_bytes(self, *, object_key: str, payload: bytes, content_type: str):
        self.objects[object_key] = (payload, content_type)
        return type(
            "Stored",
            (),
            {
                "object_key": object_key,
                "content_type": content_type,
                "content_length": len(payload),
            },
        )()


class _GarmentIdentityAnalyzerStub:
    async def analyze(self, *, job_id: str, asset_keys: list[str]):
        return type(
            "Analysis",
            (),
            {
                "garment_type": "shirt",
                "dominant_color": "white",
                "secondary_colors": ["blue"],
                "silhouette_summary": "oversized button-up shirt",
                "preserved_details": ["long sleeves", "front buttons"],
                "confidence": 0.91,
            },
        )()


class _FailingGarmentIdentityAnalyzerStub:
    async def analyze(self, *, job_id: str, asset_keys: list[str]):
        raise GarmentIdentityAnalysisFailure(safe_code="garment_identity_provider_unavailable")


class _ClickEventServiceStub:
    def __init__(self, *, redirect_allowed: bool = True, redirect_url: str | None = "https://seller.example/products/product-1") -> None:
        self.last_request = None
        self.redirect_allowed = redirect_allowed
        self.redirect_url = redirect_url

    async def record_click(self, request):
        self.last_request = request
        return type(
            "ClickResponse",
            (),
            {
                "event_id": "similar_click_1",
                "redirect_allowed": self.redirect_allowed,
                "redirect_url": self.redirect_url,
            },
        )()


def test_similar_search_route_returns_structured_results(monkeypatch) -> None:
    from src.entrypoints import similar_search_routes

    monkeypatch.setattr(
        similar_search_routes,
        "similar_search_runtime_dependencies",
        lambda settings: type("Runtime", (), {"workflow_service": _ServiceStub()})(),
    )

    response = client.post(
        "/api/similar-search",
        json={
            "source_type": "text",
            "query_text": "black midi dress with belt",
            "budget_max": 120.0,
            "reference_price": 150.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["product_id"] == "product-1"
    assert response.json()["results"][0]["offer_url"] == "https://seller.example/products/product-1"


def test_similar_search_garment_photo_route_builds_backend_owned_garment_request(monkeypatch) -> None:
    from src.entrypoints import similar_search_routes

    service = _ServiceStub()
    storage = _ObjectStorageStub()
    monkeypatch.setattr(
        similar_search_routes,
        "similar_search_runtime_dependencies",
        lambda settings: type(
            "Runtime",
            (),
            {
                "workflow_service": service,
                "object_storage": storage,
                "object_storage_root_prefix": "fitfabrica",
                "garment_identity_analyzer": _GarmentIdentityAnalyzerStub(),
            },
        )(),
    )

    response = client.post(
        "/api/similar-search/garment-photo",
        data={"budget_max": "20000", "user_country_code": "KZ", "user_city": "Almaty"},
        files={"garment_photo": ("shirt.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["product_id"] == "product-1"
    assert service.last_request.source_type == "garment_photo"
    assert service.last_request.garment_profile.garment_type == "shirt"
    assert service.last_request.user_city == "Almaty"
    assert len(storage.objects) == 1


def test_similar_search_garment_photo_route_returns_structured_analysis_failure(monkeypatch) -> None:
    from src.entrypoints import similar_search_routes

    storage = _ObjectStorageStub()
    monkeypatch.setattr(
        similar_search_routes,
        "similar_search_runtime_dependencies",
        lambda settings: type(
            "Runtime",
            (),
            {
                "workflow_service": _ServiceStub(),
                "object_storage": storage,
                "object_storage_root_prefix": "fitfabrica",
                "garment_identity_analyzer": _FailingGarmentIdentityAnalyzerStub(),
            },
        )(),
    )

    response = client.post(
        "/api/similar-search/garment-photo",
        files={"garment_photo": ("shirt.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "garment_identity_provider_unavailable"
    assert response.json()["error"]["details"]["job_id"].startswith("similar_")


def test_similar_search_click_event_route_records_interest(monkeypatch) -> None:
    from src.entrypoints import similar_search_routes

    click_service = _ClickEventServiceStub()
    monkeypatch.setattr(
        similar_search_routes,
        "similar_search_runtime_dependencies",
        lambda settings: type("Runtime", (), {"click_event_service": click_service})(),
    )

    response = client.post(
        "/api/similar-search/events/click",
        json={
            "product_id": "product-1",
            "title": "Black midi dress",
            "marketplace": "local_catalog",
            "offer_url": "https://seller.example/products/product-1",
            "image_url": "/api/business/products/product-1/images/primary",
            "user_country_code": "KZ",
            "user_city": "Almaty",
        },
    )

    assert response.status_code == 200
    assert response.json()["event_id"] == "similar_click_1"
    assert response.json()["redirect_allowed"] is True
    assert click_service.last_request.product_id == "product-1"


def test_similar_search_redirect_records_click_and_redirects(monkeypatch) -> None:
    from src.entrypoints import similar_search_routes

    click_service = _ClickEventServiceStub()
    monkeypatch.setattr(
        similar_search_routes,
        "similar_search_runtime_dependencies",
        lambda settings: type("Runtime", (), {"click_event_service": click_service})(),
    )

    response = client.get(
        "/api/similar-search/redirect",
        params={
            "product_id": "product-1",
            "title": "Black midi dress",
            "marketplace": "local_catalog",
            "offer_url": "https://seller.example/products/product-1",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "https://seller.example/products/product-1"
    assert click_service.last_request.marketplace == "local_catalog"


def test_similar_search_redirect_blocks_local_only_offer(monkeypatch) -> None:
    from src.entrypoints import similar_search_routes

    click_service = _ClickEventServiceStub(redirect_allowed=False, redirect_url=None)
    monkeypatch.setattr(
        similar_search_routes,
        "similar_search_runtime_dependencies",
        lambda settings: type("Runtime", (), {"click_event_service": click_service})(),
    )

    response = client.get(
        "/api/similar-search/redirect",
        params={
            "product_id": "product-1",
            "title": "Black midi dress",
            "marketplace": "local_catalog",
            "offer_url": "local://business-catalog/product-1",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "similar_search_offer_local_only"
