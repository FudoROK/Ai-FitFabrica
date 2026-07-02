"""Versioned provider price configuration for workflow cost estimates."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, ConfigDict, Field

COST_CONFIG_VERSION = "provider_prices.gemini.2026-06-16.v1"
GOOGLE_GEMINI_PRICING_SOURCE = "https://ai.google.dev/gemini-api/docs/pricing"
INTERNAL_MARKUP_MULTIPLIER = Decimal("1.20")


class ProviderModelPrice(BaseModel):
    """One versioned provider/model price record."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    input_text_price_per_1m_tokens_usd: Decimal = Field(ge=Decimal("0"))
    output_text_price_per_1m_tokens_usd: Decimal = Field(ge=Decimal("0"))
    image_input_price_unit: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    image_output_price_unit: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    image_generation_price_unit: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    currency: str = "USD"
    effective_date: str = "2026-06-16"
    source_note: str = Field(min_length=1)
    config_version: str = COST_CONFIG_VERSION


_SOURCE_NOTE = (
    "Official Google Gemini API pricing page; text/image/video token prices captured on 2026-06-16: "
    f"{GOOGLE_GEMINI_PRICING_SOURCE}"
)

_PRICE_TABLE: dict[tuple[str, str], ProviderModelPrice] = {
    (
        "gemini",
        "gemini-2.5-flash",
    ): ProviderModelPrice(
        provider="gemini",
        model="gemini-2.5-flash",
        input_text_price_per_1m_tokens_usd=Decimal("0.30"),
        output_text_price_per_1m_tokens_usd=Decimal("2.50"),
        image_input_price_unit=Decimal("0"),
        image_output_price_unit=Decimal("0"),
        image_generation_price_unit=Decimal("0"),
        source_note=_SOURCE_NOTE,
    ),
    (
        "gemini_structured",
        "gemini-2.5-flash",
    ): ProviderModelPrice(
        provider="gemini_structured",
        model="gemini-2.5-flash",
        input_text_price_per_1m_tokens_usd=Decimal("0.30"),
        output_text_price_per_1m_tokens_usd=Decimal("2.50"),
        image_input_price_unit=Decimal("0"),
        image_output_price_unit=Decimal("0"),
        image_generation_price_unit=Decimal("0"),
        source_note=_SOURCE_NOTE,
    ),
    (
        "gemini",
        "gemini-2.5-flash-lite",
    ): ProviderModelPrice(
        provider="gemini",
        model="gemini-2.5-flash-lite",
        input_text_price_per_1m_tokens_usd=Decimal("0.10"),
        output_text_price_per_1m_tokens_usd=Decimal("0.40"),
        image_input_price_unit=Decimal("0"),
        image_output_price_unit=Decimal("0"),
        image_generation_price_unit=Decimal("0"),
        source_note=_SOURCE_NOTE,
    ),
    (
        "google_vertex",
        "virtual-try-on-estimate",
    ): ProviderModelPrice(
        provider="google_vertex",
        model="virtual-try-on-estimate",
        input_text_price_per_1m_tokens_usd=Decimal("0"),
        output_text_price_per_1m_tokens_usd=Decimal("0"),
        image_generation_price_unit=Decimal("0.04"),
        source_note=(
            "Configurable internal estimate for virtual try-on generation; replace with provider SKU when available."
        ),
    ),
}


def get_provider_model_price(*, provider: str, model: str) -> ProviderModelPrice:
    """Return one configured provider/model price or fail closed."""

    key = (provider, model)
    if key not in _PRICE_TABLE:
        raise KeyError(f"Unknown provider model price: {provider}/{model}")
    return _PRICE_TABLE[key]


def list_provider_model_prices() -> list[ProviderModelPrice]:
    """Return the configured provider/model prices in stable order."""

    return [_PRICE_TABLE[key] for key in sorted(_PRICE_TABLE)]


def estimate_provider_cost_usd(
    *,
    price: ProviderModelPrice,
    input_tokens: int = 0,
    output_tokens: int = 0,
    image_inputs: int = 0,
    image_outputs: int = 0,
    image_generation_outputs: int = 0,
) -> Decimal:
    """Estimate provider cost in USD for one model invocation."""

    token_cost = (
        Decimal(max(0, input_tokens)) / Decimal("1000000") * price.input_text_price_per_1m_tokens_usd
        + Decimal(max(0, output_tokens)) / Decimal("1000000") * price.output_text_price_per_1m_tokens_usd
    )
    image_cost = (
        Decimal(max(0, image_inputs)) * price.image_input_price_unit
        + Decimal(max(0, image_outputs)) * price.image_output_price_unit
        + Decimal(max(0, image_generation_outputs)) * price.image_generation_price_unit
    )
    return _money(token_cost + image_cost)


def estimate_internal_cost_usd(provider_cost_usd: Decimal) -> Decimal:
    """Estimate internal cost with platform overhead reserve."""

    return _money(provider_cost_usd * INTERNAL_MARKUP_MULTIPLIER)


def _money(value: Decimal) -> Decimal:
    """Normalize money values to six decimals for reproducible reports."""

    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
