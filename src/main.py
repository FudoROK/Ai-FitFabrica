"""FastAPI webhook service bootstrap."""
from __future__ import annotations

from fastapi import FastAPI

from .entrypoints.http_routes import router as http_router
from .entrypoints.runtime_dependencies import (
    dialog_service,
    memory_summary_service,
    safe_memory_summary_response,
)
from .settings import load_settings

app = FastAPI(title="AI Assistant Skeleton Backend")
settings = load_settings()
app.state.settings = settings
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
