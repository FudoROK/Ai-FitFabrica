from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from src.domain.contracts.crm import CRMContract
from . import hubspot_client as client
from .hubspot_mapper import (
    HUBSPOT_MEMORY_PROPERTY_NAMES,
    HUBSPOT_PROFILE_FIELD_MAPPING,
    build_contact_properties,
    build_memory_properties,
)

logger = logging.getLogger(__name__)


class HubSpotCRMAdapter(CRMContract):
    def find_contact(self, *, external_user_id: str) -> Optional[str]:
        return client.search_contact_by_telegram_id(external_user_id)

    def create_contact(self, *, external_user_id: str, first_name: Optional[str] = None) -> Optional[str]:
        return client.create_contact(external_user_id, first_name)

    def update_contact(self, *, contact_id: str, properties: dict[str, Any]) -> None:
        client.update_contact(contact_id, properties)

    def append_note(self, *, contact_id: str, note: str) -> Optional[str]:
        logger.info("HubSpotCRMAdapter append_note skeleton", extra={"contact_id": contact_id})
        return None

    def create_deal(self, *, contact_id: str, payload: dict[str, Any]) -> Optional[str]:
        logger.info("HubSpotCRMAdapter create_deal skeleton", extra={"contact_id": contact_id})
        return None

    def update_stage(self, *, deal_id: str, stage: str) -> None:
        logger.info("HubSpotCRMAdapter update_stage skeleton", extra={"deal_id": deal_id, "stage": stage})

    def get_contact(self, *, contact_id: str, properties: list[str]) -> Optional[dict[str, Any]]:
        return client.get_contact(contact_id, properties)

    def build_profile_properties(
        self,
        *,
        profile: Mapping[str, object],
        existing_properties: Mapping[str, object] | None = None,
    ) -> dict[str, Any]:
        return build_contact_properties(profile, existing_properties=existing_properties)

    def profile_property_names(self) -> list[str]:
        return [provider_field for _, provider_field in HUBSPOT_PROFILE_FIELD_MAPPING]

    def memory_properties(
        self,
        *,
        daily_text: Optional[str],
        daily_date: Optional[str],
        rolling_text: Optional[str],
        rolling_version: Optional[int],
        rolling_hash: Optional[str],
    ) -> dict[str, Any]:
        return build_memory_properties(
            daily_text=daily_text,
            daily_date=daily_date,
            rolling_text=rolling_text,
            rolling_version=rolling_version,
            rolling_hash=rolling_hash,
        )

    def memory_property_names(self) -> list[str]:
        return list(HUBSPOT_MEMORY_PROPERTY_NAMES)

    def is_enabled(self) -> bool:
        return client.hubspot_enabled()
