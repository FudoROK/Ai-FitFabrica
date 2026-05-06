"""Domain-level lead patch preparation for persistence."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from src.domain.extraction.lead_patch_canon import compose_lead_update_payload
from src.domain.models import Lead
from src.adapters.external_apis.google_maps.contracts import TimezoneResolverContract
from src.adapters.external_apis.google_maps.timezone_resolver import GoogleMapsTimezoneResolver
from src.services.timezone import DeterministicTimezoneResolver, TimezoneResolutionInput, TimezoneResolver

logger = logging.getLogger(__name__)


class LeadPatchPreparationService:
    """Prepare canonical lead patches before repository persistence."""

    def __init__(
        self,
        *,
        timezone_resolver: Optional[TimezoneResolver] = None,
        geo_timezone_resolver: Optional[TimezoneResolverContract] = None,
    ) -> None:
        self._timezone_resolver = timezone_resolver or DeterministicTimezoneResolver()
        self._geo_timezone_resolver = geo_timezone_resolver or self._build_default_geo_timezone_resolver()

    @staticmethod
    def _build_default_geo_timezone_resolver() -> Optional[TimezoneResolverContract]:
        maps_api_key = (os.getenv("MAPS_API_KEY") or "").strip()
        if not maps_api_key:
            return None
        return GoogleMapsTimezoneResolver()

    def compose(self, *, lead_patch: dict[str, object], existing_lead: Optional[Lead]) -> dict[str, object]:
        existing_profile = (
            existing_lead.lead_profile
            if existing_lead and isinstance(existing_lead.lead_profile, dict)
            else {}
        )
        payload = compose_lead_update_payload(
            dict(lead_patch or {}),
            existing_profile=existing_profile,
        )
        lead_id = existing_lead.lead_id if existing_lead else None
        self._enrich_timezone_fields(payload, lead_id=lead_id, existing_lead=existing_lead)
        return payload

    def _enrich_timezone_fields(
        self,
        payload: dict[str, object],
        *,
        lead_id: Optional[str],
        existing_lead: Optional[Lead],
    ) -> None:
        logger.info(
            "timezone_resolution_started",
            extra={
                "lead_id": lead_id,
                "has_city": bool(payload.get("city")),
                "has_country": bool(payload.get("country")),
                "has_input_timezone": bool(payload.get("timezone")),
            },
        )
        city = payload.get("city")
        country = payload.get("country")
        input_timezone = payload.get("timezone")

        if isinstance(input_timezone, str):
            input_timezone = input_timezone.strip() or None
        else:
            input_timezone = None
        if isinstance(city, str):
            city = city.strip() or None
        else:
            city = None
        if isinstance(country, str):
            country = country.strip() or None
        else:
            country = None

        if self._should_preserve_existing_geo(existing_lead=existing_lead, city=city, country=country):
            logger.info(
                "timezone_resolution_geo_preserved",
                extra={
                    "lead_id": lead_id,
                    "incoming_city": city,
                    "incoming_country": country,
                    "existing_city": getattr(existing_lead, "city", None),
                    "existing_country": getattr(existing_lead, "country", None),
                },
            )
            payload.pop("city", None)
            payload.pop("country", None)
            payload.pop("timezone", None)
            payload.pop("timezone_source", None)
            payload.pop("timezone_confidence", None)
            payload.pop("timezone_updated_at", None)
            return

        existing_city = self._normalize_optional_string(getattr(existing_lead, "city", None))
        existing_country = self._normalize_optional_string(getattr(existing_lead, "country", None))
        effective_city = city or existing_city
        effective_country = country or existing_country

        resolved = self._timezone_resolver.resolve(
            TimezoneResolutionInput(city=effective_city, country=effective_country, timezone=input_timezone)
        )

        if city:
            payload["city"] = city
        if country:
            payload["country"] = country

        if not resolved.resolved:
            external_timezone = self._resolve_timezone_via_geo_adapter(
                city=effective_city,
                country=effective_country,
                lead_id=lead_id,
            )
            if external_timezone:
                logger.info(
                    "timezone_resolution_succeeded_external",
                    extra={
                        "lead_id": lead_id,
                        "has_city": True,
                        "has_country": True,
                        "has_input_timezone": bool(input_timezone),
                        "source": "backend_resolved_from_city_country",
                        "reason": "resolved_via_geo_timezone_adapter",
                    },
                )
                payload["timezone_source"] = "backend_resolved_from_city_country"
                payload["timezone_confidence"] = 0.9
                payload["timezone_updated_at"] = datetime.now(timezone.utc)
                payload["timezone"] = external_timezone
                return

            if input_timezone:
                logger.warning(
                    "timezone_resolution_failed_validation",
                    extra={
                        "lead_id": lead_id,
                        "has_city": bool(city),
                        "has_country": bool(country),
                        "has_input_timezone": True,
                        "source": resolved.source,
                        "reason": resolved.reason,
                    },
                )
            elif resolved.reason in {"city_country_not_found_or_ambiguous", "city_only_ambiguous_or_unknown"}:
                logger.warning(
                    "timezone_resolution_ambiguous",
                    extra={
                        "lead_id": lead_id,
                        "has_city": bool(city),
                        "has_country": bool(country),
                        "has_input_timezone": False,
                        "source": resolved.source,
                        "reason": resolved.reason,
                    },
                )
            else:
                logger.info(
                    "timezone_resolution_skipped",
                    extra={
                        "lead_id": lead_id,
                        "has_city": bool(city),
                        "has_country": bool(country),
                        "has_input_timezone": bool(input_timezone),
                        "source": resolved.source,
                        "reason": resolved.reason,
                    },
                )
            if existing_lead and isinstance(existing_lead.timezone, str) and existing_lead.timezone.strip():
                return
            return

        logger.info(
            "timezone_resolution_succeeded",
            extra={
                "lead_id": lead_id,
                "has_city": bool(city),
                "has_country": bool(country),
                "has_input_timezone": bool(input_timezone),
                "source": resolved.source,
                "reason": resolved.reason,
            },
        )
        payload["timezone_source"] = resolved.source
        payload["timezone_confidence"] = resolved.confidence
        payload["timezone_updated_at"] = datetime.now(timezone.utc)
        payload["timezone"] = resolved.timezone if resolved.resolved else None

    def _resolve_timezone_via_geo_adapter(
        self,
        *,
        city: Optional[str],
        country: Optional[str],
        lead_id: Optional[str],
    ) -> Optional[str]:
        if not city or not country:
            return None
        if self._geo_timezone_resolver is None:
            return None

        try:
            timezone_name = self._geo_timezone_resolver.resolve(city, country)
        except Exception:
            logger.exception(
                "timezone_resolution_external_failed",
                extra={"lead_id": lead_id, "city": city, "country": country},
            )
            return None

        if not isinstance(timezone_name, str):
            return None
        normalized = timezone_name.strip()
        if not self._is_valid_iana_timezone(normalized):
            logger.warning(
                "timezone_resolution_external_invalid",
                extra={"lead_id": lead_id, "city": city, "country": country},
            )
            return None
        return normalized

    @staticmethod
    def _is_valid_iana_timezone(value: str) -> bool:
        try:
            ZoneInfo(value)
        except Exception:
            return False
        return "/" in value

    @staticmethod
    def _normalize_optional_string(value: object) -> Optional[str]:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _should_preserve_existing_geo(
        self,
        *,
        existing_lead: Optional[Lead],
        city: Optional[str],
        country: Optional[str],
    ) -> bool:
        if existing_lead is None:
            return False
        if not city or not country:
            return False

        existing_city = existing_lead.city.strip() if isinstance(existing_lead.city, str) else None
        existing_country = existing_lead.country.strip() if isinstance(existing_lead.country, str) else None
        if not existing_city or not existing_country:
            return False

        return (existing_city.casefold(), existing_country.casefold()) != (
            city.casefold(),
            country.casefold(),
        )
