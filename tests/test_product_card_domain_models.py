from src.domain.product_card import ProductCardDraft, ProductCardRequest


def test_product_card_request_keeps_target_channel_and_brand_tone() -> None:
    request = ProductCardRequest(
        title_hint="Linen midi dress",
        target_channel="wildberries",
        brand_tone="minimal premium",
    )

    assert request.target_channel == "wildberries"
    assert request.brand_tone == "minimal premium"


def test_product_card_draft_exposes_structured_marketplace_fields() -> None:
    draft = ProductCardDraft(
        title="Linen midi dress",
        description="Breathable summer dress with a clean silhouette.",
        bullet_points=["linen blend", "midi length"],
        attributes={"category": "dress"},
    )

    assert draft.attributes["category"] == "dress"
