from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from src.settings import load_settings
from .contracts import TimezoneResolverContract

logger = logging.getLogger(__name__)

_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_TIMEZONE_URL = "https://maps.googleapis.com/maps/api/timezone/json"
_DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class GoogleMapsTimezoneResolver(TimezoneResolverContract):
    """Google Maps adapter for deterministic timezone resolution by city and country."""

    def __init__(self, *, http_client: httpx.Client | None = None, timeout: httpx.Timeout | None = None) -> None:
        self._http_client = http_client or httpx.Client(timeout=timeout or _DEFAULT_TIMEOUT)
        self._owns_client = http_client is None

    def close(self) -> None:
        if self._owns_client:
            self._http_client.close()

    def resolve(self, city: str, country: str) -> Optional[str]:
        normalized_city = city.strip() if isinstance(city, str) else ""
        normalized_country = country.strip() if isinstance(country, str) else ""

        logger.info(
            "timezone resolution started",
            extra={"city": normalized_city, "country": normalized_country},
        )

        if not normalized_city or not normalized_country:
            logger.info(
                "timezone resolution skipped due to invalid input",
                extra={"city": normalized_city, "country": normalized_country, "reason": "empty_or_non_string_input"},
            )
            return None

        api_key = (load_settings().maps_api_key or "").strip()
        if not api_key:
            logger.warning(
                "timezone resolution failed",
                extra={"city": normalized_city, "country": normalized_country, "reason": "maps_api_key_missing"},
            )
            return None

        query = f"{normalized_city}, {normalized_country}"
        location = self._geocode(query=query, api_key=api_key, city=normalized_city, country=normalized_country)
        if not location:
            return None

        timezone_id = self._lookup_timezone(
            lat=location[0],
            lng=location[1],
            api_key=api_key,
            city=normalized_city,
            country=normalized_country,
        )
        if not timezone_id:
            return None

        logger.info(
            "timezone resolved successfully",
            extra={"city": normalized_city, "country": normalized_country},
        )
        return timezone_id

    def _geocode(self, *, query: str, api_key: str, city: str, country: str) -> Optional[tuple[float, float]]:
        try:
            response = self._http_client.get(_GEOCODING_URL, params={"address": query, "key": api_key})
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "geocoding request failed",
                extra={"city": city, "country": country, "reason": type(exc).__name__},
            )
            return None
        except ValueError:
            logger.warning(
                "geocoding response parsing failed",
                extra={"city": city, "country": country, "reason": "invalid_json"},
            )
            return None

        if payload.get("status") != "OK":
            logger.info(
                "geocoding returned no results",
                extra={"city": city, "country": country, "reason": "status_not_ok"},
            )
            return None

        results = payload.get("results")
        if not isinstance(results, list) or not results:
            logger.info(
                "geocoding returned no results",
                extra={"city": city, "country": country, "reason": "empty_results"},
            )
            return None

        first_result = results[0] if isinstance(results[0], dict) else None
        location = (first_result or {}).get("geometry", {}).get("location", {}) if first_result else {}
        lat = location.get("lat") if isinstance(location, dict) else None
        lng = location.get("lng") if isinstance(location, dict) else None
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            logger.info(
                "geocoding returned invalid location",
                extra={"city": city, "country": country, "reason": "invalid_lat_lng"},
            )
            return None

        return float(lat), float(lng)

    def _lookup_timezone(self, *, lat: float, lng: float, api_key: str, city: str, country: str) -> Optional[str]:
        timestamp = int(time.time())
        try:
            response = self._http_client.get(
                _TIMEZONE_URL,
                params={
                    "location": f"{lat},{lng}",
                    "timestamp": timestamp,
                    "key": api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "timezone lookup failed",
                extra={"city": city, "country": country, "reason": type(exc).__name__},
            )
            return None
        except ValueError:
            logger.warning(
                "timezone response parsing failed",
                extra={"city": city, "country": country, "reason": "invalid_json"},
            )
            return None

        if payload.get("status") != "OK":
            logger.info(
                "timezone lookup failed",
                extra={"city": city, "country": country, "reason": "status_not_ok"},
            )
            return None

        timezone_id = payload.get("timeZoneId")
        if not isinstance(timezone_id, str) or not timezone_id.strip():
            logger.info(
                "timezone lookup failed",
                extra={"city": city, "country": country, "reason": "invalid_timezone_id"},
            )
            return None

        return timezone_id.strip()
