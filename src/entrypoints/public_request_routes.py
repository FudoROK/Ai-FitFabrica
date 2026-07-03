"""FastAPI routes for public website forms."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.adapters.database.sql.public_request_repositories import SqlDemoRequestRepository
from src.adapters.public_requests import InMemoryDemoRequestRepository
from src.domain.public_requests import DemoRequest, PublicEmail
from src.entrypoints.runtime_dependencies import portable_infrastructure
from src.settings import Settings
from src.use_cases.public_requests import PublicRequestService


router = APIRouter(tags=["public-requests"])


class DemoRequestPayload(BaseModel):
    """Payload submitted from the public contact/demo form."""

    name: str = Field(min_length=1, max_length=255)
    email: PublicEmail
    company: str | None = Field(default=None, max_length=255)
    message: str | None = Field(default=None, max_length=4000)


class DemoRequestResponse(BaseModel):
    """Response returned after a public demo/contact request is persisted."""

    ok: bool
    request_id: str
    status: str


class SignInPayload(BaseModel):
    """Public sign-in payload."""

    email: PublicEmail
    password: str = Field(min_length=1, max_length=1024)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""

    return request.app.state.settings


def _service(settings: Settings) -> PublicRequestService:
    """Return the cached public request service for this runtime."""

    service = getattr(settings, "_public_request_service", None)
    if isinstance(service, PublicRequestService):
        return service

    infrastructure = portable_infrastructure(settings)
    if infrastructure.sql_session_factory is not None:
        repository = SqlDemoRequestRepository(infrastructure.sql_session_factory)
    else:
        repository = InMemoryDemoRequestRepository()

    service = PublicRequestService(repository=repository)
    setattr(settings, "_public_request_service", service)
    return service


@router.post("/demo-request", response_model=DemoRequestResponse)
async def create_demo_request(payload: DemoRequestPayload, request: Request) -> DemoRequestResponse:
    """Persist one public demo/contact request without invoking AI or billing."""

    created: DemoRequest = await _service(_settings(request)).create_demo_request(
        name=payload.name,
        email=payload.email,
        company=payload.company,
        message=payload.message,
    )
    return DemoRequestResponse(ok=True, request_id=created.request_id, status=created.status)


@router.post("/auth/sign-in")
async def sign_in(payload: SignInPayload, request: Request) -> JSONResponse:
    """Fail closed until production authentication is configured."""

    result = await _service(_settings(request)).sign_in(email=payload.email)
    return JSONResponse(
        status_code=503,
        content={
            "ok": result.ok,
            "error": {
                "code": result.code,
                "message": result.message,
            },
        },
    )
