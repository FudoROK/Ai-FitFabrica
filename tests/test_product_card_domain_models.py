from src.domain.product_card import ProductCardDraft, ProductCardGarmentAnalysis, ProductCardRequest


def test_product_card_request_keeps_target_channel_and_brand_tone() -> None:
    request = ProductCardRequest(
        title_hint="Linen midi dress",
        category="dress",
        target_channel="wildberries",
        brand_tone="minimal premium",
    )

    assert request.category == "dress"
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


def test_product_card_garment_analysis_keeps_strict_reusable_visual_facts() -> None:
    analysis = ProductCardGarmentAnalysis(
        job_id="product_card_1",
        invocation_id="invocation_1",
        prompt_version="garment_identity.v1",
        contract_version="garment_identity.contract.v1",
        garment_type="coat",
        dominant_color="khaki",
        secondary_colors=["brown"],
        silhouette_summary="Relaxed hooded coat.",
        preserved_details=["front buttons", "patch pockets"],
        confidence=0.95,
        limitations=[],
        visual_details=[
            {
                "detail_type": "button",
                "description": "Front button closure.",
                "confidence": 0.97,
            }
        ],
        evidence=[
            {
                "source_type": "artifact",
                "source_ref": "product/source.webp",
                "observation": "Button closure is visible.",
                "confidence": 0.97,
            }
        ],
        uncertainty_level="low",
        unknowns=[],
    )

    assert analysis.garment_type == "coat"
    assert analysis.visual_details[0].detail_type == "button"
