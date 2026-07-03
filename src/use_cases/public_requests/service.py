"""Backend-owned public website request use cases."""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from src.domain.public_requests import AuthLogoutResult, AuthSessionState, DemoRequest, SignInAttemptResult


class DemoRequestRepository(Protocol):
    """Persistence port for public demo/contact requests."""

    async def save_demo_request(self, request: DemoRequest) -> DemoRequest:
        """Persist one demo/contact request."""


class PublicRequestService:
    """Handle public website form submissions without frontend business logic."""

    def __init__(self, *, repository: DemoRequestRepository) -> None:
        """Store service dependencies."""

        self._repository = repository

    async def create_demo_request(
        self,
        *,
        name: str,
        email: str,
        company: str | None,
        message: str | None,
    ) -> DemoRequest:
        """Validate and persist one public demo/contact request."""

        request = DemoRequest(
            request_id=f"demo_req_{uuid4().hex}",
            name=name.strip(),
            email=email,
            company=_optional_text(company),
            message=_optional_text(message),
        )
        return await self._repository.save_demo_request(request)

    async def sign_in(self, *, email: str) -> SignInAttemptResult:
        """Return a fail-closed sign-in result until production auth is configured."""

        del email
        return SignInAttemptResult()

    async def get_auth_session(self) -> AuthSessionState:
        """Return the current unauthenticated state until production auth is configured."""

        return AuthSessionState()

    async def logout(self) -> AuthLogoutResult:
        """Return an idempotent logout result without requiring an active session."""

        return AuthLogoutResult()


def _optional_text(value: str | None) -> str | None:
    """Normalize optional public form text."""

    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
