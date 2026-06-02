"""FastAPI service bootstrap."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .entrypoints.http_routes import build_http_router
from .entrypoints.runtime_dependencies import (
    dialog_service,
    memory_summary_service,
    safe_memory_summary_response,
)
from .settings import Settings
from .settings import load_settings


def configure_cors(target_app: FastAPI, target_settings: Settings) -> None:
    """Allow configured browser frontend origins to call backend-owned API endpoints."""
    if not target_settings.cors_allowed_origins and not target_settings.cors_allowed_origin_regex:
        return

    target_app.add_middleware(
        CORSMiddleware,
        allow_origins=target_settings.cors_allowed_origins,
        allow_origin_regex=target_settings.cors_allowed_origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


def build_app(target_settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app for one runtime settings profile."""
    settings = target_settings or load_settings()
    target_app = FastAPI(title="AI FitFabrica Backend")
    target_app.state.settings = settings
    configure_cors(target_app, settings)
    target_app.include_router(build_http_router())
    return target_app


settings = load_settings()
app = build_app(settings)


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
