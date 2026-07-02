from __future__ import annotations

from pathlib import Path


PRODUCT_AGENT_DIRS = [
    "src/adk_agents/orchestrator_agent",
    "src/adk_agents/user_profile_agent",
    "src/adk_agents/business_profile_agent",
    "src/adk_agents/human_identity_agent",
    "src/adk_agents/garment_identity_agent",
    "src/adk_agents/material_texture_agent",
    "src/adk_agents/try_on_agent",
    "src/adk_agents/quality_verifier_agent",
    "src/adk_agents/repair_agent",
    "src/adk_agents/fashion_stylist_agent",
    "src/adk_agents/marketplace_agent",
    "src/adk_agents/trend_agent",
    "src/adk_agents/pricing_agent",
    "src/adk_agents/product_card_agent",
    "src/adk_agents/cost_credits_agent",
]


def test_fitfabrica_agent_runtime_bundle_does_not_expose_removed_or_temporary_agents() -> None:
    text = Path("src/entrypoints/runtime_dependencies.py").read_text(encoding="utf-8")

    assert "fitfabrica_agent_runtime_dependencies" in text
    assert "primary_root_agent" not in text
    assert "daily_memory_agent_tmp20260425_024853" not in text


def test_product_agent_packages_do_not_import_each_other_directly() -> None:
    forbidden_tokens = [
        "human_identity_agent",
        "garment_identity_agent",
        "material_texture_agent",
        "try_on_agent",
        "quality_verifier_agent",
        "repair_agent",
        "fashion_stylist_agent",
        "marketplace_agent",
        "trend_agent",
        "pricing_agent",
        "product_card_agent",
        "cost_credits_agent",
    ]

    for package_dir in PRODUCT_AGENT_DIRS:
        package_name = Path(package_dir).name
        for path in Path(package_dir).glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if path.name == "__init__.py":
                continue
            assert "src.adk_agents." not in text
            for token in forbidden_tokens:
                if token == package_name:
                    continue
                assert token not in text


def test_temporary_daily_memory_agent_package_is_removed_from_active_tree() -> None:
    assert not Path("src/adk_agents/daily_memory_agent_tmp20260425_024853").exists()


def test_removed_primary_adk_agent_package_is_absent_from_active_tree() -> None:
    assert not Path("src/adk_agents/primary_agent").exists()
