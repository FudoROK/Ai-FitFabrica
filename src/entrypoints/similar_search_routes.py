"""FastAPI routes for backend-owned similar search."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.domain.similar_search import SimilarSearchRequest, SimilarSearchResponse
from src.entrypoints.runtime_dependencies import similar_search_runtime_dependencies
from src.settings import Settings

router = APIRouter()


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


@router.post("/api/similar-search", response_model=SimilarSearchResponse)
async def create_similar_search(
    request: SimilarSearchRequest,
    settings: Annotated[Settings, Depends(_settings)],
) -> SimilarSearchResponse:
    """Execute backend-owned similar search and return structured results."""
    runtime = similar_search_runtime_dependencies(settings)
    return await runtime.workflow_service.search(request)
