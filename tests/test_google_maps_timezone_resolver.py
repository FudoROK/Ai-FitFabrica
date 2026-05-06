from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import httpx

from src.adapters.external_apis.google_maps.timezone_resolver import GoogleMapsTimezoneResolver


class _ResponseStub:
    def __init__(self, *, json_payload=None, json_error: Exception | None = None, status_code: int = 200):
        self._json_payload = json_payload
        self._json_error = json_error
        self._status_code = status_code
        self._request = httpx.Request("GET", "https://example.com")

    def raise_for_status(self) -> None:
        if self._status_code >= 400:
            raise httpx.HTTPStatusError("http error", request=self._request, response=httpx.Response(self._status_code))

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._json_payload


def _resolver(monkeypatch, *, client_get_side_effect):
    client = Mock()
    client.get.side_effect = client_get_side_effect
    monkeypatch.setattr(
        "src.adapters.external_apis.google_maps.timezone_resolver.load_settings",
        lambda: SimpleNamespace(maps_api_key="maps-key"),
    )
    return GoogleMapsTimezoneResolver(http_client=client), client


def test_resolve_success(monkeypatch):
    resolver, client = _resolver(
        monkeypatch,
        client_get_side_effect=[
            _ResponseStub(
                json_payload={
                    "status": "OK",
                    "results": [{"geometry": {"location": {"lat": 52.52, "lng": 13.405}}}],
                }
            ),
            _ResponseStub(json_payload={"status": "OK", "timeZoneId": "Europe/Berlin"}),
        ],
    )

    result = resolver.resolve(city="Berlin", country="Germany")

    assert result == "Europe/Berlin"
    assert client.get.call_count == 2


def test_resolve_empty_input_returns_none_without_http_calls(monkeypatch):
    resolver, client = _resolver(monkeypatch, client_get_side_effect=[])

    assert resolver.resolve(city="", country="Germany") is None
    assert resolver.resolve(city="Berlin", country="   ") is None
    assert client.get.call_count == 0


def test_resolve_returns_none_when_geocoding_has_no_results(monkeypatch):
    resolver, client = _resolver(
        monkeypatch,
        client_get_side_effect=[_ResponseStub(json_payload={"status": "ZERO_RESULTS", "results": []})],
    )

    result = resolver.resolve(city="Berlin", country="Germany")

    assert result is None
    assert client.get.call_count == 1


def test_resolve_returns_none_when_timezone_status_not_ok(monkeypatch):
    resolver, client = _resolver(
        monkeypatch,
        client_get_side_effect=[
            _ResponseStub(
                json_payload={
                    "status": "OK",
                    "results": [{"geometry": {"location": {"lat": 52.52, "lng": 13.405}}}],
                }
            ),
            _ResponseStub(json_payload={"status": "INVALID_REQUEST"}),
        ],
    )

    result = resolver.resolve(city="Berlin", country="Germany")

    assert result is None
    assert client.get.call_count == 2


def test_resolve_returns_none_on_geocoding_network_error(monkeypatch):
    request = httpx.Request("GET", "https://example.com")
    resolver, client = _resolver(
        monkeypatch,
        client_get_side_effect=httpx.RequestError("network", request=request),
    )

    result = resolver.resolve(city="Berlin", country="Germany")

    assert result is None
    assert client.get.call_count == 1


def test_resolve_returns_none_on_timezone_network_error(monkeypatch):
    request = httpx.Request("GET", "https://example.com")
    resolver, client = _resolver(
        monkeypatch,
        client_get_side_effect=[
            _ResponseStub(
                json_payload={
                    "status": "OK",
                    "results": [{"geometry": {"location": {"lat": 52.52, "lng": 13.405}}}],
                }
            ),
            httpx.RequestError("network", request=request),
        ],
    )

    result = resolver.resolve(city="Berlin", country="Germany")

    assert result is None
    assert client.get.call_count == 2


def test_resolve_returns_none_on_invalid_json_structure(monkeypatch):
    resolver, client = _resolver(
        monkeypatch,
        client_get_side_effect=[
            _ResponseStub(json_error=ValueError("bad json")),
        ],
    )

    result = resolver.resolve(city="Berlin", country="Germany")

    assert result is None
    assert client.get.call_count == 1
