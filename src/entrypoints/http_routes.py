"""HTTP transport router aggregator for entrypoint route modules."""
from __future__ import annotations

from fastapi import APIRouter

from src.settings import load_settings

from .content_package_routes import router as content_package_router
from .credits_routes import router as credits_router
from .internal_task_routes import router as internal_task_router
from .pricing_routes import router as pricing_router
from .product_card_routes import router as product_card_router
from .similar_search_routes import router as similar_search_router
from .status_routes import router as status_router
from .try_on_routes import router as try_on_router


def build_http_router() -> APIRouter:
    """Build the active HTTP surface for one runtime profile."""
    router = APIRouter()
    router.include_router(internal_task_router)
    router.include_router(status_router)
    router.include_router(credits_router)
    router.include_router(try_on_router)
    router.include_router(similar_search_router)
    router.include_router(product_card_router)
    router.include_router(content_package_router)
    router.include_router(pricing_router)
    return router


router = build_http_router()
