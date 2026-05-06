from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class MessagingContract(ABC):
    @abstractmethod
    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def edit_message(self, chat_id: int | str, message_id: str, text: str, **kwargs: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_buttons(self, chat_id: int | str, text: str, buttons: list[dict[str, Any]], **kwargs: Any) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def send_media(self, chat_id: int | str, media_url: str, caption: Optional[str] = None, **kwargs: Any) -> Optional[str]:
        raise NotImplementedError
