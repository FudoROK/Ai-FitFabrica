from src.use_cases.pricing.ranking import recommend_price


def test_recommend_price_returns_market_band_and_recommendation() -> None:
    result = recommend_price(comparables=[3990.0, 4590.0, 5990.0], desired_margin_percent=30.0, currency="RUB")
    assert result.market_avg == 4590.0
    assert result.recommended_price > 0
