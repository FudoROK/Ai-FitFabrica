from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.adk_agents.business_profile_agent import BusinessProfileContract
from src.adk_agents.cost_credits_agent import CostCreditsExplanationContract, CreditChargeComponent
from src.adk_agents.fashion_stylist_agent import FashionStylistNoteContract
from src.adk_agents.garment_identity_agent import GarmentIdentityContract
from src.adk_agents.human_identity_agent import HumanIdentityContract, HumanIdentityPreservationTarget
from src.adk_agents.marketplace_agent import MarketplaceSearchStrategyContract
from src.adk_agents.material_texture_agent import MaterialTextureContract
from src.adk_agents.orchestrator_agent import OrchestratorDecisionContract
from src.adk_agents.pricing_agent import PricingRecommendationContract
from src.adk_agents.product_card_agent import ProductCardContentContract
from src.adk_agents.quality_verifier_agent import QualityVerifierDecisionContract
from src.adk_agents.repair_agent import RepairInstructionContract
from src.adk_agents.trend_agent import TrendSignalContract
from src.adk_agents.try_on_agent import TryOnInstructionContract
from src.adk_agents.user_profile_agent import UserProfileContract


def test_human_identity_contract_exposes_backend_preservation_targets() -> None:
    contract = HumanIdentityContract(
        face_visibility="fully_visible",
        pose_summary="front-facing standing pose",
        body_region_visibility=["face", "torso", "arms"],
        preservation_targets=[
            HumanIdentityPreservationTarget(
                attribute_name="face",
                preservation_reason="identity consistency for final try-on result",
            )
        ],
        confidence=0.94,
        limitations=["lower legs are cropped"],
    )

    assert contract.preservation_targets[0].attribute_name == "face"
    assert contract.confidence == pytest.approx(0.94)


def test_garment_identity_contract_keeps_structured_preserved_details() -> None:
    contract = GarmentIdentityContract(
        garment_type="dress",
        dominant_color="black",
        silhouette_summary="fitted midi dress",
        preserved_details=["belt", "collar", "sleeve length"],
        confidence=0.88,
        limitations=["back view not visible"],
    )

    assert contract.garment_type == "dress"
    assert "belt" in contract.preserved_details


def test_material_texture_contract_requires_evidence_note() -> None:
    contract = MaterialTextureContract(
        visible_material_signals=["soft drape", "low sheen"],
        texture_signals=["smooth surface", "light folds"],
        evidence_note="Texture estimate is based only on visible folds and surface reflection.",
        confidence=0.61,
        limitations=["material composition cannot be confirmed from image alone"],
    )

    assert contract.evidence_note.startswith("Texture estimate")


def test_try_on_instruction_contract_is_backend_consumable() -> None:
    contract = TryOnInstructionContract(
        instruction_summary="Preserve face and pose while aligning the garment silhouette to the body.",
        garment_focus_points=["waist fit", "collar", "hem length"],
        styling_focus_points=["balanced proportions", "clean neckline"],
        confidence=0.9,
        limitations=["garment back panel is inferred from front view only"],
    )

    assert contract.preserve_face is True
    assert "waist fit" in contract.garment_focus_points


def test_quality_verifier_decision_contract_supports_repair_recommended() -> None:
    contract = QualityVerifierDecisionContract(
        verdict="repair_recommended",
        summary="Hands and collar need a local repair pass before user exposure.",
        blocking_issues=[],
        repair_targets=["hands", "collar"],
        confidence=0.78,
        limitations=["decision is based on backend verification facts only"],
    )

    assert contract.verdict == "repair_recommended"
    assert contract.repair_targets == ["hands", "collar"]


def test_repair_instruction_contract_returns_editing_steps() -> None:
    contract = RepairInstructionContract(
        repair_scope="local",
        target_issues=["missing collar structure", "hand artifact"],
        editing_instructions=[
            "restore collar edge continuity",
            "repair fingers without changing pose",
        ],
        confidence=0.73,
        limitations=["logo restoration is not requested in this pass"],
    )

    assert contract.repair_scope == "local"
    assert len(contract.editing_instructions) == 2


def test_fashion_stylist_note_contract_returns_structured_note_and_tips() -> None:
    contract = FashionStylistNoteContract(
        note="The silhouette reads balanced and the waist definition works well for this look.",
        outfit_tips=["Pair with a structured blazer", "Use minimal jewelry around the neckline"],
        confidence=0.84,
        limitations=["Final advice does not confirm real-world fabric comfort"],
    )

    assert contract.note
    assert contract.outfit_tips[0].startswith("Pair")


def test_orchestrator_decision_contract_returns_backend_routing_fields() -> None:
    contract = OrchestratorDecisionContract(
        workflow_type="try_on",
        requested_capabilities=["human_identity", "garment_identity", "stylist_note"],
        required_inputs=["human_photo", "garment_photo"],
        confidence=0.91,
        limitations=["user style profile is not available in this request"],
    )

    assert contract.workflow_type == "try_on"
    assert "garment_identity" in contract.requested_capabilities


def test_user_profile_contract_summarizes_b2c_preferences() -> None:
    contract = UserProfileContract(
        style_preferences=["minimal", "smart casual"],
        size_signals=["prefers relaxed fit"],
        budget_preference="mid-range",
        fit_preferences=["waist definition", "comfortable sleeves"],
        confidence=0.79,
        limitations=["profile derived from sparse history"],
    )

    assert contract.budget_preference == "mid-range"
    assert "minimal" in contract.style_preferences


def test_business_profile_contract_summarizes_b2b_context() -> None:
    contract = BusinessProfileContract(
        brand_style=["clean studio visuals", "premium basics"],
        target_channels=["marketplace", "instagram"],
        content_rules=["avoid oversized text overlays", "keep product color accurate"],
        pricing_positioning="accessible premium",
        confidence=0.83,
        limitations=["merchant seasonal campaign context is missing"],
    )

    assert contract.pricing_positioning == "accessible premium"
    assert "marketplace" in contract.target_channels


def test_marketplace_search_strategy_contract_returns_retrieval_guidance() -> None:
    contract = MarketplaceSearchStrategyContract(
        retrieval_intent="find visually similar premium-casual dresses under the requested budget",
        comparison_axes=["silhouette", "color", "price"],
        source_constraints=["approved marketplace feeds only"],
        budget_filters=["under 120 USD"],
        confidence=0.82,
        limitations=["brand-level availability may change between refreshes"],
    )

    assert contract.comparison_axes[0] == "silhouette"
    assert "approved marketplace feeds only" in contract.source_constraints


def test_trend_signal_contract_returns_structured_actions() -> None:
    contract = TrendSignalContract(
        trend_summary="Minimal structured tailoring continues to outperform loud seasonal prints.",
        target_audience="premium basics shoppers",
        recommended_actions=["highlight clean silhouettes", "prioritize neutral palette merchandising"],
        confidence=0.77,
        limitations=["signal reflects currently supplied backend evidence only"],
    )

    assert contract.target_audience == "premium basics shoppers"
    assert len(contract.recommended_actions) == 2


def test_pricing_recommendation_contract_returns_backend_consumable_reasoning() -> None:
    contract = PricingRecommendationContract(
        pricing_positioning="accessible premium",
        recommended_price_band="89-109 USD",
        evidence_highlights=["quality details exceed budget tier baseline", "comparable median sits near 99 USD"],
        confidence=0.81,
        limitations=["promo elasticity is not modeled in this output"],
    )

    assert contract.recommended_price_band == "89-109 USD"
    assert "comparable median" in contract.evidence_highlights[1]


def test_product_card_content_contract_returns_structured_b2b_copy() -> None:
    contract = ProductCardContentContract(
        title="Structured midi dress with clean waist definition",
        short_description="Premium-casual midi dress designed for clean studio presentation and accurate color retention.",
        key_attributes=["midi length", "defined waist", "clean neckline"],
        merchandising_notes=["prioritize front silhouette in hero image", "keep copy aligned with premium basics tone"],
        confidence=0.83,
        limitations=["fabric composition label is not available in source evidence"],
    )

    assert contract.title.startswith("Structured")
    assert "midi length" in contract.key_attributes


def test_cost_credits_explanation_contract_returns_structured_charge_components() -> None:
    contract = CostCreditsExplanationContract(
        workflow_type="try_on",
        charge_components=[
            CreditChargeComponent(
                component_name="generation",
                rationale="primary image generation pass",
            ),
            CreditChargeComponent(
                component_name="quality_verification",
                rationale="post-generation verification before result exposure",
            ),
        ],
        total_credit_estimate=14,
        confidence=0.8,
        limitations=["final ledger amount remains backend-authoritative"],
    )

    assert contract.total_credit_estimate == 14
    assert contract.charge_components[0].component_name == "generation"


def test_wave1_agent_contracts_forbid_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        HumanIdentityContract(
            face_visibility="visible",
            pose_summary="standing",
            confidence=0.5,
            limitations=[],
            unexpected_field="forbidden",
        )
