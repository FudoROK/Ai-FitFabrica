from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from src.domain.extraction import non_empty_patch
from src.domain.extraction.lead_patch_canon import canonicalize_lead_patch
from src.domain.models import Lead
from src.llm.vertex.vertex_schema_validator import AGENT_OUTPUT_SCHEMA
from src.services.inbound.lead_patch_preparation_service import LeadPatchPreparationService
from src.services.timezone import DeterministicTimezoneResolver, TimezoneResolutionInput
from src.use_cases.lead.ingest_lead_patch_use_case import IngestLeadPatchUseCase


def test_agent_output_schema_keeps_primary_agent_lead_patch_minimal() -> None:
    lead_patch_schema = AGENT_OUTPUT_SCHEMA["properties"]["system_payload"]["properties"]["lead_patch"]["properties"]
    assert tuple(lead_patch_schema.keys()) == ("first_name",)


def test_canonicalize_lead_patch_keeps_city_country_and_valid_timezone_only() -> None:
    canonical = canonicalize_lead_patch(
        {
            "city": "  New York ",
            "country": "  United States ",
            "timezone": "America/New_York",
        }
    )
    assert canonical["city"] == "New York"
    assert canonical["country"] == "United States"
    assert canonical["timezone"] == "America/New_York"

    invalid_timezone = canonicalize_lead_patch({"timezone": "GMT+6 probably"})
    assert "timezone" not in invalid_timezone


def test_non_empty_patch_keeps_city_country_and_valid_timezone() -> None:
    merged = non_empty_patch(
        {},
        {
            "city": "Berlin",
            "country": "Germany",
            "timezone": "Europe/Berlin",
        },
    )
    assert merged["city"] == "Berlin"
    assert merged["country"] == "Germany"
    assert merged["timezone"] == "Europe/Berlin"


def test_non_empty_patch_drops_invalid_timezone() -> None:
    merged = non_empty_patch(
        {},
        {
            "city": "Berlin",
            "country": "Germany",
            "timezone": "UTC+6 maybe",
        },
    )
    assert merged["city"] == "Berlin"
    assert merged["country"] == "Germany"
    assert "timezone" not in merged


def test_timezone_resolver_accepts_explicit_valid_timezone() -> None:
    resolver = DeterministicTimezoneResolver()
    result = resolver.resolve(
        TimezoneResolutionInput(
            city=None,
            country=None,
            timezone="Europe/Moscow",
        )
    )
    assert result.resolved is True
    assert result.timezone == "Europe/Moscow"
    assert result.source == "user_explicit"
    assert result.confidence == 1.0


def test_timezone_resolver_city_country_and_city_only_paths() -> None:
    resolver = DeterministicTimezoneResolver()

    city_country = resolver.resolve(TimezoneResolutionInput(city="Berlin", country="Germany"))
    assert city_country.resolved is True
    assert city_country.timezone == "Europe/Berlin"
    assert city_country.source == "backend_resolved_from_city_country"

    city_only = resolver.resolve(TimezoneResolutionInput(city="Berlin", country=None))
    assert city_only.resolved is True
    assert city_only.timezone == "Europe/Berlin"
    assert city_only.source == "backend_resolved_from_city_only"

    ambiguous = resolver.resolve(TimezoneResolutionInput(city="Springfield", country=None))
    assert ambiguous.resolved is False
    assert ambiguous.timezone is None

    insufficient = resolver.resolve(TimezoneResolutionInput(city=None, country=None))
    assert insufficient.resolved is False
    assert insufficient.timezone is None


def test_timezone_resolver_accepts_cyrillic_city_country_aliases() -> None:
    resolver = DeterministicTimezoneResolver()

    result = resolver.resolve(TimezoneResolutionInput(city="Москва", country="Россия"))

    assert result.resolved is True
    assert result.timezone == "Europe/Moscow"
    assert result.source == "backend_resolved_from_city_country"


def test_lead_patch_preparation_sets_timezone_backend_side() -> None:
    service = LeadPatchPreparationService()
    payload = service.compose(
        lead_patch={"city": "Berlin", "country": "Germany"},
        existing_lead=Lead(lead_id="lead-1", lead_profile={}),
    )

    assert payload["city"] == "Berlin"
    assert payload["country"] == "Germany"
    assert payload["timezone"] == "Europe/Berlin"
    assert payload["timezone_source"] == "backend_resolved_from_city_country"
    assert payload["timezone_confidence"] == 1.0
    assert isinstance(payload["timezone_updated_at"], datetime)
    assert payload["timezone_updated_at"].tzinfo == timezone.utc


def test_lead_patch_preparation_does_not_wipe_existing_timezone_when_resolution_fails() -> None:
    service = LeadPatchPreparationService()
    existing_lead = Lead(
        lead_id="lead-1",
        timezone="America/New_York",
        timezone_source="user_explicit",
        timezone_confidence=1.0,
        lead_profile={},
    )

    payload = service.compose(
        lead_patch={"city": "Unknown City"},
        existing_lead=existing_lead,
    )
    assert payload["city"] == "Unknown City"
    assert "timezone" not in payload
    assert "timezone_source" not in payload
    assert "timezone_confidence" not in payload
    assert "timezone_updated_at" not in payload


def test_lead_patch_preparation_resolves_timezone_with_split_location_updates() -> None:
    service = LeadPatchPreparationService()
    existing_lead = Lead(
        lead_id="lead-1",
        city="Berlin",
        lead_profile={},
    )

    payload = service.compose(
        lead_patch={"country": "Germany"},
        existing_lead=existing_lead,
    )

    assert payload["country"] == "Germany"
    assert payload["timezone"] == "Europe/Berlin"
    assert payload["timezone_source"] == "backend_resolved_from_city_country"
    assert payload["timezone_confidence"] == 1.0
    assert isinstance(payload["timezone_updated_at"], datetime)
    assert payload["timezone_updated_at"].tzinfo == timezone.utc


def test_lead_patch_preparation_preserves_existing_geo_on_conflicting_location_patch() -> None:
    service = LeadPatchPreparationService()
    existing_lead = Lead(
        lead_id="lead-1",
        city="Алматы",
        country="Казахстан",
        timezone="Asia/Almaty",
        timezone_source="backend_resolved_from_city_country",
        timezone_confidence=1.0,
        lead_profile={},
    )

    payload = service.compose(
        lead_patch={"city": "Москва", "country": "Россия"},
        existing_lead=existing_lead,
    )

    assert "city" not in payload
    assert "country" not in payload
    assert "timezone" not in payload
    assert "timezone_source" not in payload
    assert "timezone_confidence" not in payload
    assert "timezone_updated_at" not in payload


class _CaptureLeadRepo:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def apply_lead_patch(self, lead_id: str, patch: dict[str, object]) -> bool:
        self.calls.append((lead_id, patch))
        return True


class _GeoTimezoneResolverStub:
    def __init__(self, timezone_name: str | None) -> None:
        self.timezone_name = timezone_name

    def resolve(self, city: str, country: str) -> str | None:
        return self.timezone_name


def test_ingest_pipeline_keeps_location_and_uses_backend_timezone_contract() -> None:
    repo = _CaptureLeadRepo()
    use_case = IngestLeadPatchUseCase(leads_repo=repo)

    result = asyncio.run(
        use_case.execute(
            lead_id="lead-1",
            payload={
                "lead_patch": {
                    "city": "Berlin",
                    "country": "Germany",
                    "timezone": "Europe/Berlin",
                }
            },
            external_user_id="u-1",
        )
    )
    assert result is True
    assert len(repo.calls) == 1
    _, patch = repo.calls[0]
    assert patch["city"] == "Berlin"
    assert patch["country"] == "Germany"
    assert patch["timezone"] == "Europe/Berlin"
    assert patch["channel_user_id"] == "u-1"


def test_lead_patch_preparation_uses_geo_adapter_fallback_for_unknown_city_country() -> None:
    service = LeadPatchPreparationService(
        geo_timezone_resolver=_GeoTimezoneResolverStub("Asia/Bishkek"),
    )

    payload = service.compose(
        lead_patch={"city": "Bishkek", "country": "Kyrgyzstan"},
        existing_lead=Lead(lead_id="lead-1", lead_profile={}),
    )

    assert payload["city"] == "Bishkek"
    assert payload["country"] == "Kyrgyzstan"
    assert payload["timezone"] == "Asia/Bishkek"
    assert payload["timezone_source"] == "backend_resolved_from_city_country"
    assert payload["timezone_confidence"] == 0.9


def test_lead_patch_preparation_drops_invalid_geo_adapter_timezone() -> None:
    service = LeadPatchPreparationService(
        geo_timezone_resolver=_GeoTimezoneResolverStub("UTC+6"),
    )

    payload = service.compose(
        lead_patch={"city": "Bishkek", "country": "Kyrgyzstan"},
        existing_lead=Lead(lead_id="lead-1", lead_profile={}),
    )

    assert payload["city"] == "Bishkek"
    assert payload["country"] == "Kyrgyzstan"
    assert "timezone" not in payload
    assert "timezone_source" not in payload
    assert "timezone_confidence" not in payload
