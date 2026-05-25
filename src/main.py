"""FastAPI webhook service bootstrap."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .entrypoints.http_routes import router as http_router
from .entrypoints.runtime_dependencies import (
    dialog_service,
    memory_summary_service,
    safe_memory_summary_response,
)
from .settings import Settings
from .settings import load_settings


def configure_cors(target_app: FastAPI, target_settings: Settings) -> None:
    """Allow configured browser frontend origins to call backend-owned API endpoints."""
    if not target_settings.cors_allowed_origins:
        return

    target_app.add_middleware(
        CORSMiddleware,
        allow_origins=target_settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


app = FastAPI(title="AI Assistant Skeleton Backend")
settings = load_settings()
app.state.settings = settings
configure_cors(app, settings)
app.include_router(http_router)


# Backward-compatible test shims.
def _dialog_service():
    return dialog_service(app.state.settings)


def _memory_summary_service():
    return memory_summary_service(app.state.settings)


def _safe_memory_summary_response(*, result):
    return safe_memory_summary_response(result=result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=settings.app_host, port=settings.app_port, reload=False)
