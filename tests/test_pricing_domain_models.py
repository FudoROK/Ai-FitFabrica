from src.domain.pricing import PricingRecommendation, PricingRequest


def test_pricing_request_keeps_target_margin_and_currency() -> None:
    request = PricingRequest(
        product_id="product-1",
        target_currency="RUB",
        desired_margin_percent=30.0,
    )

    assert request.target_currency == "RUB"
    assert request.desired_margin_percent == 30.0


def test_pricing_recommendation_exposes_recommended_price_and_reasoning() -> None:
    recommendation = PricingRecommendation(
        recommended_price=4490.0,
        currency="RUB",
        rationale="Positioned slightly below premium comparable cluster.",
        market_min=3990.0,
        market_avg=4590.0,
        market_max=5990.0,
    )

    assert recommendation.market_avg == 4590.0
