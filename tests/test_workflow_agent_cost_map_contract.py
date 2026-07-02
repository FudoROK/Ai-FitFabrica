from __future__ import annotations

from pathlib import Path


REQUIRED_COST_MAP_COLUMNS = [
    "workflow_type",
    "step_order",
    "step_name",
    "agent_name",
    "provider",
    "model",
    "input_type",
    "output_type",
    "required",
    "can_retry",
    "can_repair",
    "charged_to_user",
    "free_if_failed",
    "expected_input_tokens",
    "expected_output_tokens",
    "expected_image_inputs",
    "expected_image_outputs",
    "expected_provider_cost_usd",
    "expected_internal_cost_usd",
    "notes",
]


def test_workflow_agent_cost_map_document_covers_required_workflows_and_columns() -> None:
    text = Path("docs/costs/workflow_agent_cost_map_v1.md").read_text(encoding="utf-8")

    for workflow_type in [
        "try_on",
        "product_card",
        "similar_search",
        "outfit_recommendation",
        "pricing",
        "content_package",
    ]:
        assert workflow_type in text
    for column in REQUIRED_COST_MAP_COLUMNS:
        assert column in text


def test_credits_policy_and_pricing_documents_exist_with_core_terms() -> None:
    policy_text = Path("docs/costs/credits_policy_v1.md").read_text(encoding="utf-8")
    pricing_text = Path("docs/costs/credits_pricing_table_v1.md").read_text(encoding="utf-8")

    assert "Human Identity blocked unsuitable photo" in policy_text
    assert "provider/system error" in policy_text
    assert "1 credit = 50 KZT" in pricing_text
    assert "recommended_credits_balanced" in pricing_text


def test_cost_map_separates_repair_marketplace_and_backend_service_costs() -> None:
    text = Path("docs/costs/workflow_agent_cost_map_v1.md").read_text(encoding="utf-8")

    for required_step in [
        "repair_instruction",
        "repair_image_generation",
        "second_quality_verifier",
        "marketplace_connector_cost",
        "external_api_cost_usd",
        "parser/proxy/search cost",
        "no-result search cost",
        "user_profile_backend_service",
        "business_profile_backend_service",
    ]:
        assert required_step in text


def test_pricing_table_separates_product_card_and_content_package_variants() -> None:
    pricing_text = Path("docs/costs/credits_pricing_table_v1.md").read_text(encoding="utf-8")

    for product_action in [
        "B2B Product Card Text Only",
        "B2B Product Card + 1 Model Photo",
        "B2B Product Card + Model Photo + Quality Verification",
        "B2B Product Card + Content Package",
        "Content Package Text Only",
        "Content Package + 1 Generated Image",
        "Content Package + 3 Generated Images",
        "Content Package + 5 Generated Images",
    ]:
        assert product_action in pricing_text


def test_recalibration_report_requirements_are_documented() -> None:
    pricing_text = Path("docs/costs/credits_pricing_table_v1.md").read_text(encoding="utf-8")

    for metric in [
        "actual avg Try-On cost",
        "actual avg Product Card cost",
        "repair rate",
        "retry rate",
        "failed free job cost",
        "real margin by workflow",
    ]:
        assert metric in pricing_text


def test_provider_prices_are_not_hardcoded_inside_workflow_code() -> None:
    workflow_files = [
        Path("src/use_cases/try_on/workflow_service.py"),
        Path("src/use_cases/try_on/workflow_execution.py"),
        Path("src/use_cases/product_card/workflow_service.py"),
        Path("src/use_cases/content_package/workflow_service.py"),
        Path("src/use_cases/pricing/workflow_service.py"),
    ]

    forbidden_fragments = ["0.30", "2.50", "0.04", "provider_prices.gemini"]
    for path in workflow_files:
        text = path.read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in text, f"{fragment} must stay out of {path}"
