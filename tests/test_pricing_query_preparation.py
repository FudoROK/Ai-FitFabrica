from src.domain.pricing import PricingRequest
from src.use_cases.pricing.query_preparation import build_pricing_brief


def test_pricing_brief_keeps_product_and_margin_context() -> None:
    brief = build_pricing_brief(
        PricingRequest(product_id="product-1", target_currency="RUB", desired_margin_percent=30.0)
    )

    assert brief.product_id == "product-1"
    assert brief.desired_margin_percent == 30.0
