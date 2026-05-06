"""Telegram Bot API client with connection reuse and logging."""
from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, Dict, Optional

import httpx

from src.settings import load_settings
from src.utils.log_redaction import redact

logger = logging.getLogger(__name__)


class TelegramClient:
    """Thin async wrapper around Telegram sendMessage endpoint."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self.settings = load_settings()
        self._client = httpx.AsyncClient(timeout=timeout, base_url=self.settings.telegram_api_base)

    def _method_path(self, method: str) -> str:
        return f"/bot{self.settings.telegram_bot_token}/{method}"

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = True,
    ) -> None:
        payload: Dict[str, Any] = {
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        started = perf_counter()
        try:
            response = await self._client.post(self._method_path("sendMessage"), json=payload)
            response.raise_for_status()
            logger.info(
                "telegram_send_message_done",
                extra={
                    "task": "telegram_send_message",
                    "status": "ok",
                    "provider": "telegram",
                    "latency_ms": int((perf_counter() - started) * 1000),
                    "retry_count": 0,
                },
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "telegram_send_message_http_error",
                extra={
                    "task": "telegram_send_message",
                    "status": "failed",
                    "provider": "telegram",
                    "latency_ms": int((perf_counter() - started) * 1000),
                    "retry_count": 0,
                    "error_type": "http_status_error",
                    "status_code": exc.response.status_code,
                    "error_summary": redact(exc.response.text)[:200],
                },
            )
            raise
        except httpx.HTTPError as exc:  # pragma: no cover - network
            logger.error(
                "telegram_send_message_network_error",
                extra={
                    "task": "telegram_send_message",
                    "status": "failed",
                    "provider": "telegram",
                    "latency_ms": int((perf_counter() - started) * 1000),
                    "retry_count": 0,
                    "error_type": type(exc).__name__,
                    "error_summary": redact(exc)[:200],
                },
            )
            raise

    async def close(self) -> None:
        await self._client.aclose()
