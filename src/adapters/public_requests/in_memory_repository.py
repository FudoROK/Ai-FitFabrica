"""In-memory fallback for public demo/contact requests."""

from __future__ import annotations

from src.domain.public_requests import DemoRequest


class InMemoryDemoRequestRepository:
    """Store public demo/contact requests in memory for tests and local runtime."""

    def __init__(self) -> None:
        """Initialize an empty request store."""

        self._requests: dict[str, DemoRequest] = {}

    async def save_demo_request(self, request: DemoRequest) -> DemoRequest:
        """Persist one demo/contact request in memory."""

        self._requests[request.request_id] = request
        return request

    async def list_demo_requests(self) -> list[DemoRequest]:
        """Return stored demo/contact requests for tests."""

        return list(self._requests.values())
