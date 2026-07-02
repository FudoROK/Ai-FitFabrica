from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class _OutfitBuilderServiceStub:
    async def get_brief(self):
        return {
            "workflow": "outfit_builder",
            "status": "active",
            "hero_title": "Подбор образа",
            "hero_description": "Backend вернул живой brief для outfit-builder workflow.",
            "input_sections": [
                "Базовая вещь",
                "Случай",
                "Бюджет",
            ],
            "result_sections": [
                "3-5 образов",
                "Пояснения стилиста",
                "Похожие товары",
            ],
            "readiness_note": "Следующий шаг — real submit contract для запуска рекомендаций.",
        }

    async def create_request(self, *, occasion: str, budget: str | None, base_item: str | None):
        return {
            "request_id": "outfit_req_123",
            "workflow": "outfit_builder",
            "status": "accepted",
            "occasion": occasion,
            "budget": budget,
            "base_item": base_item,
            "message": "Outfit-builder request accepted. Recommendation pipeline is not wired yet.",
            "status_url": "/api/workspace/outfit-builder/requests/outfit_req_123/status",
            "created_at": None,
        }

    async def list_recent_requests(self):
        return [
            {
                "request_id": "outfit_req_123",
                "workflow": "outfit_builder",
                "status": "completed",
                "occasion": "office",
                "budget": "150",
                "base_item": "black blazer",
                "message": "Outfit recommendations are ready for review.",
                "status_url": "/api/workspace/outfit-builder/requests/outfit_req_123/status",
                "created_at": None,
            }
        ]

    async def get_request_status(self, *, request_id: str):
        return {
            "request_id": request_id,
            "workflow": "outfit_builder",
            "status": "completed",
            "status_history": [
                {
                    "status": "accepted",
                    "message": "Outfit-builder request accepted.",
                    "occurred_at": "2026-06-12T10:00:00Z",
                },
                {
                    "status": "completed",
                    "message": "Outfit recommendations are ready for review.",
                    "occurred_at": "2026-06-12T10:00:02Z",
                },
            ],
            "result_summary": {
                "headline": "3 outfit directions prepared",
                "summary_lines": [
                    "Office-smart base with blazer",
                    "Relaxed after-hours layer",
                    "Budget-aware alternative look",
                ],
            },
        }


def test_workspace_outfit_builder_brief_returns_backend_owned_contract(monkeypatch) -> None:
    from src.entrypoints import outfit_builder_routes

    monkeypatch.setattr(
        outfit_builder_routes,
        "_service",
        lambda _settings: _OutfitBuilderServiceStub(),
    )

    response = client.get("/api/workspace/outfit-builder/brief")

    assert response.status_code == 200
    assert response.json() == {
        "workflow": "outfit_builder",
        "status": "active",
        "hero_title": "Подбор образа",
        "hero_description": "Backend вернул живой brief для outfit-builder workflow.",
        "input_sections": ["Базовая вещь", "Случай", "Бюджет"],
        "result_sections": ["3-5 образов", "Пояснения стилиста", "Похожие товары"],
        "readiness_note": "Следующий шаг — real submit contract для запуска рекомендаций.",
    }


def test_workspace_outfit_builder_request_returns_accepted_contract(monkeypatch) -> None:
    from src.entrypoints import outfit_builder_routes

    monkeypatch.setattr(
        outfit_builder_routes,
        "_service",
        lambda _settings: _OutfitBuilderServiceStub(),
    )

    response = client.post(
        "/api/workspace/outfit-builder/requests",
        json={
            "occasion": "office",
            "budget": "150",
            "base_item": "black blazer",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "request_id": "outfit_req_123",
        "workflow": "outfit_builder",
        "status": "accepted",
        "occasion": "office",
        "budget": "150",
        "base_item": "black blazer",
        "message": "Outfit-builder request accepted. Recommendation pipeline is not wired yet.",
        "status_url": "/api/workspace/outfit-builder/requests/outfit_req_123/status",
        "created_at": None,
    }


def test_workspace_outfit_builder_recent_requests_returns_backend_owned_history(monkeypatch) -> None:
    from src.entrypoints import outfit_builder_routes

    monkeypatch.setattr(
        outfit_builder_routes,
        "_service",
        lambda _settings: _OutfitBuilderServiceStub(),
    )

    response = client.get("/api/workspace/outfit-builder/requests")

    assert response.status_code == 200
    assert response.json() == {
        "workflow": "outfit_builder",
        "requests": [
            {
                "request_id": "outfit_req_123",
                "workflow": "outfit_builder",
                "status": "completed",
                "occasion": "office",
                "budget": "150",
                "base_item": "black blazer",
                "message": "Outfit recommendations are ready for review.",
                "status_url": "/api/workspace/outfit-builder/requests/outfit_req_123/status",
                "created_at": None,
            }
        ],
    }


def test_workspace_outfit_builder_status_returns_backend_owned_progress(monkeypatch) -> None:
    from src.entrypoints import outfit_builder_routes

    monkeypatch.setattr(
        outfit_builder_routes,
        "_service",
        lambda _settings: _OutfitBuilderServiceStub(),
    )

    response = client.get("/api/workspace/outfit-builder/requests/outfit_req_123/status")

    assert response.status_code == 200
    assert response.json() == {
        "request_id": "outfit_req_123",
        "workflow": "outfit_builder",
        "status": "completed",
        "status_history": [
            {
                "status": "accepted",
                "message": "Outfit-builder request accepted.",
                "occurred_at": "2026-06-12T10:00:00Z",
            },
            {
                "status": "completed",
                "message": "Outfit recommendations are ready for review.",
                "occurred_at": "2026-06-12T10:00:02Z",
            },
        ],
        "result_summary": {
            "headline": "3 outfit directions prepared",
            "summary_lines": [
                "Office-smart base with blazer",
                "Relaxed after-hours layer",
                "Budget-aware alternative look",
            ],
        },
    }
