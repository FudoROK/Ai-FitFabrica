"""SQL repositories for public website requests."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.public_requests import DemoRequest

from .public_request_models import PublicDemoRequestRow


class SqlDemoRequestRepository:
    """Persist public demo/contact requests in SQL."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Store the SQL session factory."""

        self._session_factory = session_factory

    async def save_demo_request(self, request: DemoRequest) -> DemoRequest:
        """Persist one demo/contact request."""

        async with self._session_factory() as session:
            async with session.begin():
                session.add(
                    PublicDemoRequestRow(
                        request_id=request.request_id,
                        name=request.name,
                        email=str(request.email),
                        company=request.company,
                        message=request.message,
                        status=request.status,
                        created_at=request.created_at,
                    )
                )
        return request
