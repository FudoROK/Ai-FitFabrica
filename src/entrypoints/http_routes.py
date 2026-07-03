"""HTTP transport router aggregator for entrypoint route modules."""
from __future__ import annotations

from fastapi import APIRouter

from .admin_business_catalog_routes import router as admin_business_catalog_router
from .admin_cost_routes import router as admin_cost_router
from .admin_taxonomy_routes import router as admin_taxonomy_router
from .business_catalog_routes import router as business_catalog_router
from .content_package_routes import router as content_package_router
from .credits_routes import router as credits_router
from .garment_taxonomy_routes import router as garment_taxonomy_router
from .outfit_builder_routes import router as outfit_builder_router
from .pricing_routes import router as pricing_router
from .product_card_routes import router as product_card_router
from .public_request_routes import router as public_request_router
from .similar_search_routes import router as similar_search_router
from .status_routes import router as status_router
from .try_on_routes import router as try_on_router
from .workspace_capability_routes import router as workspace_capability_router
from .workspace_integration_routes import router as workspace_integration_router
from .workspace_routes import router as workspace_router
from .workspace_profile_routes import router as workspace_profile_router


def build_http_router() -> APIRouter:
    """Build the active HTTP surface for one runtime profile."""
    router = APIRouter()
    router.include_router(status_router)
    router.include_router(public_request_router)
    router.include_router(admin_business_catalog_router)
    router.include_router(admin_cost_router)
    router.include_router(admin_taxonomy_router)
    router.include_router(business_catalog_router)
    router.include_router(garment_taxonomy_router)
    router.include_router(workspace_router)
    router.include_router(workspace_capability_router)
    router.include_router(workspace_profile_router)
    router.include_router(workspace_integration_router)
    router.include_router(credits_router)
    router.include_router(outfit_builder_router)
    router.include_router(try_on_router)
    router.include_router(similar_search_router)
    router.include_router(product_card_router)
    router.include_router(content_package_router)
    router.include_router(pricing_router)
    return router


router = build_http_router()
