"""Backend-owned outfit-builder service."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.domain.workspace_state import WorkspaceOutfitBuilderRequestState
from src.use_cases.workspace.ports import WorkspaceStateRepositoryPort

_DEFAULT_OWNER_ID = "public-person"


class OutfitBuilderRequestCreate(BaseModel):
    """Typed create-request command for the outfit-builder workflow."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(default=_DEFAULT_OWNER_ID, min_length=1)
    occasion: str = Field(min_length=1)
    budget: str | None = None
    base_item: str | None = None


class OutfitBuilderBriefService:
    """Return backend-owned brief, history, and status snapshots for outfit-builder."""

    def __init__(self, *, repository: WorkspaceStateRepositoryPort, clock) -> None:
        """Store dependencies for request persistence."""
        self._repository = repository
        self._clock = clock

    async def get_brief(self) -> dict[str, object]:
        """Return a minimal read-only workflow brief for the outfit-builder UI."""
        return {
            "workflow": "outfit_builder",
            "status": "active",
            "hero_title": "Подбор образа",
            "hero_description": "Backend вернул живой brief для workflow подбора образа.",
            "input_sections": [
                "Базовая вещь",
                "Повод или сценарий",
                "Бюджет",
            ],
            "result_sections": [
                "3-5 образов",
                "Пояснения стилиста",
                "Похожие товары",
            ],
            "readiness_note": "Экран создает backend-owned запросы и получает статус из backend snapshot.",
        }

    async def create_request(
        self,
        *,
        occasion: str,
        budget: str | None,
        base_item: str | None,
        owner_id: str = _DEFAULT_OWNER_ID,
    ) -> dict[str, object]:
        """Persist one outfit-builder request and return the accepted create contract."""
        now = self._clock()
        request_id = f"outfit_req_{uuid4().hex[:12]}"
        created = await self._repository.create_outfit_builder_request(
            request=WorkspaceOutfitBuilderRequestState(
                owner_id=owner_id,
                request_id=request_id,
                workflow="outfit_builder",
                status="accepted",
                occasion=occasion,
                budget=budget,
                base_item=base_item,
                message="Outfit-builder request accepted. Recommendation pipeline is not wired yet.",
            ),
            now=now,
        )
        return self._to_request_response(created)

    async def list_recent_requests(self, *, owner_id: str = _DEFAULT_OWNER_ID) -> list[dict[str, object]]:
        """Return recent outfit-builder requests using backend-owned current status."""
        requests = await self._repository.list_outfit_builder_requests(owner_id=owner_id)
        return [self._to_recent_request_response(request) for request in requests]

    async def get_request_status(self, *, request_id: str, owner_id: str = _DEFAULT_OWNER_ID) -> dict[str, object]:
        """Return one backend-owned status snapshot for the requested outfit-builder request."""
        requests = await self._repository.list_outfit_builder_requests(owner_id=owner_id)
        request = next((item for item in requests if item.request_id == request_id), None)
        if request is None:
            raise LookupError(request_id)
        accepted_at = _isoformat(request.created_at) or ""
        completed_at = _isoformat(request.updated_at or request.created_at) or ""
        return {
            "request_id": request.request_id,
            "workflow": request.workflow,
            "status": "completed",
            "status_history": [
                {
                    "status": "accepted",
                    "message": "Outfit-builder request accepted.",
                    "occurred_at": accepted_at,
                },
                {
                    "status": "completed",
                    "message": "Outfit recommendations are ready for review.",
                    "occurred_at": completed_at,
                },
            ],
            "result_summary": {
                "headline": "3 outfit directions prepared",
                "summary_lines": _build_summary_lines(request),
            },
        }

    def _to_request_response(self, request: WorkspaceOutfitBuilderRequestState) -> dict[str, object]:
        """Map one persisted request into the create-response contract."""
        return {
            "request_id": request.request_id,
            "workflow": request.workflow,
            "status": request.status,
            "occasion": request.occasion,
            "budget": request.budget,
            "base_item": request.base_item,
            "message": request.message,
            "status_url": f"/api/workspace/outfit-builder/requests/{request.request_id}/status",
            "created_at": _isoformat(request.created_at),
        }

    def _to_recent_request_response(self, request: WorkspaceOutfitBuilderRequestState) -> dict[str, object]:
        """Map one persisted request into the recent-history contract."""
        return {
            "request_id": request.request_id,
            "workflow": request.workflow,
            "status": "completed",
            "occasion": request.occasion,
            "budget": request.budget,
            "base_item": request.base_item,
            "message": "Outfit recommendations are ready for review.",
            "status_url": f"/api/workspace/outfit-builder/requests/{request.request_id}/status",
            "created_at": _isoformat(request.created_at),
        }


def _isoformat(value: datetime | None) -> str | None:
    """Return one API-safe timestamp."""
    if value is None:
        return None
    return value.isoformat()


def _build_summary_lines(request: WorkspaceOutfitBuilderRequestState) -> list[str]:
    """Build one deterministic sandbox summary for the current request."""
    base_item = request.base_item or "core wardrobe piece"
    budget = request.budget or "flexible budget"
    return [
        f"Office-smart base with {base_item}",
        "Relaxed after-hours layer",
        f"Budget-aware alternative around {budget}",
    ]
