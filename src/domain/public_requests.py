"""Domain models for public website requests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field


PublicEmail = Annotated[str, Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


def public_request_utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp for public requests."""

    return datetime.now(timezone.utc)


class DemoRequest(BaseModel):
    """A durable public demo/contact request submitted from the website."""

    request_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    email: PublicEmail
    company: str | None = Field(default=None, max_length=255)
    message: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="received", max_length=64)
    created_at: datetime = Field(default_factory=public_request_utc_now)


class SignInAttemptResult(BaseModel):
    """Public sign-in response for the not-yet-configured auth surface."""

    ok: bool = False
    code: str = "auth_not_configured"
    message: str = "Authentication is not configured for this environment."
