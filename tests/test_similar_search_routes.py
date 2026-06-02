from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class _ServiceStub:
    async def search(self, request):
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
                }
            ]
        }


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
