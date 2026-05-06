"""HTTP transport router aggregator for entrypoint route modules."""
from __future__ import annotations

from fastapi import APIRouter

from .internal_task_routes import router as internal_task_router
from .pubsub_routes import router as pubsub_router
from .status_routes import router as status_router
from .telegram_webhook_routes import router as telegram_webhook_router

router = APIRouter()
router.include_router(telegram_webhook_router)
router.include_router(pubsub_router)
router.include_router(internal_task_router)
router.include_router(status_router)
