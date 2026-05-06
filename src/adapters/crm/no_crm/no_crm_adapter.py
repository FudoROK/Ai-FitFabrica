from __future__ import annotations

from typing import Any, Mapping, Optional

from src.domain.contracts.crm import CRMContract


class NoCRMAdapter(CRMContract):
    def find_contact(self, *, external_user_id: str) -> Optional[str]:
        return None

    def create_contact(self, *, external_user_id: str, first_name: Optional[str] = None) -> Optional[str]:
        return None

    def update_contact(self, *, contact_id: str, properties: dict[str, Any]) -> None:
        return None

    def append_note(self, *, contact_id: str, note: str) -> Optional[str]:
        return None

    def create_deal(self, *, contact_id: str, payload: dict[str, Any]) -> Optional[str]:
        return None

    def update_stage(self, *, deal_id: str, stage: str) -> None:
        return None

    def get_contact(self, *, contact_id: str, properties: list[str]) -> Optional[dict[str, Any]]:
        return None

    def build_profile_properties(
        self,
        *,
        profile: Mapping[str, object],
        existing_properties: Mapping[str, object] | None = None,
    ) -> dict[str, Any]:
        _ = profile
        _ = existing_properties
        return {}

    def profile_property_names(self) -> list[str]:
        return []

    def memory_properties(
        self,
        *,
        daily_text: Optional[str],
        daily_date: Optional[str],
        rolling_text: Optional[str],
        rolling_version: Optional[int],
        rolling_hash: Optional[str],
    ) -> dict[str, Any]:
        _ = daily_text
        _ = daily_date
        _ = rolling_text
        _ = rolling_version
        _ = rolling_hash
        return {}

    def memory_property_names(self) -> list[str]:
        return []

    def is_enabled(self) -> bool:
        return False
