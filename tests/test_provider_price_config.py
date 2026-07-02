from __future__ import annotations

from decimal import Decimal

import pytest

from src.costs.provider_price_config import COST_CONFIG_VERSION, estimate_provider_cost_usd, get_provider_model_price


def test_gemini_flash_price_config_is_versioned_and_sourced() -> None:
    price = get_provider_model_price(provider="gemini", model="gemini-2.5-flash")

    assert price.provider == "gemini"
    assert price.model == "gemini-2.5-flash"
    assert price.input_text_price_per_1m_tokens_usd == Decimal("0.30")
    assert price.output_text_price_per_1m_tokens_usd == Decimal("2.50")
    assert price.currency == "USD"
    assert price.effective_date == "2026-06-16"
    assert price.config_version == COST_CONFIG_VERSION
    assert "ai.google.dev/gemini-api/docs/pricing" in price.source_note


def test_unknown_provider_model_price_fails_closed() -> None:
    with pytest.raises(KeyError, match="Unknown provider model price"):
        get_provider_model_price(provider="unknown", model="missing-model")


def test_provider_cost_estimate_uses_token_and_generation_units() -> None:
    price = get_provider_model_price(provider="gemini", model="gemini-2.5-flash")

    cost = estimate_provider_cost_usd(
        price=price,
        input_tokens=1_000_000,
        output_tokens=100_000,
        image_generation_outputs=1,
    )

    assert cost == Decimal("0.550000")
