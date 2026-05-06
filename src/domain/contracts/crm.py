from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional


class CRMContract(ABC):
    """Stable CRM integration contract for core runtime."""

    @abstractmethod
    def find_contact(self, *, external_user_id: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def create_contact(self, *, external_user_id: str, first_name: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def update_contact(self, *, contact_id: str, properties: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_note(self, *, contact_id: str, note: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def create_deal(self, *, contact_id: str, payload: dict[str, Any]) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def update_stage(self, *, deal_id: str, stage: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_contact(self, *, contact_id: str, properties: list[str]) -> Optional[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def build_profile_properties(
        self,
        *,
        profile: Mapping[str, object],
        existing_properties: Mapping[str, object] | None = None,
    ) -> dict[str, Any]:
        """Translate provider-neutral profile to provider-specific contact properties."""
        raise NotImplementedError

    @abstractmethod
    def profile_property_names(self) -> list[str]:
        """Return provider-specific property names needed for profile merge."""
        raise NotImplementedError

    @abstractmethod
    def memory_properties(
        self,
        *,
        daily_text: Optional[str],
        daily_date: Optional[str],
        rolling_text: Optional[str],
        rolling_version: Optional[int],
        rolling_hash: Optional[str],
    ) -> dict[str, Any]:
        """Translate memory sync payload to provider-specific contact properties."""
        raise NotImplementedError

    @abstractmethod
    def memory_property_names(self) -> list[str]:
        """Return provider-specific property names allowed for memory sync writes."""
        raise NotImplementedError

    @abstractmethod
    def is_enabled(self) -> bool:
        raise NotImplementedError
