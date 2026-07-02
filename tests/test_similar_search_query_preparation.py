from __future__ import annotations

from src.domain.similar_search import SimilarSearchGarmentProfile, SimilarSearchRequest
from src.use_cases.similar_search.query_preparation import build_similarity_query_profile, canonicalize_garment_category


def test_query_preparation_maps_text_request_into_embedding_input() -> None:
    profile = build_similarity_query_profile(
        SimilarSearchRequest(
            source_type="text",
            query_text="black midi dress with belt",
            budget_max=120.0,
        )
    )

    assert profile.embedding_input == "black midi dress with belt"
    assert profile.budget_max == 120.0


def test_query_preparation_maps_garment_profile_into_embedding_input() -> None:
    profile = build_similarity_query_profile(
        SimilarSearchRequest(
            source_type="garment_photo",
            garment_profile=SimilarSearchGarmentProfile(
                garment_type="shirt",
                dominant_color="white",
                secondary_colors=["blue"],
                silhouette_summary="oversized button-up shirt",
                preserved_details=["long sleeves", "front buttons", "spread collar"],
                confidence=0.92,
            ),
            budget_max=15000.0,
        )
    )

    assert profile.embedding_input == (
        "garment_type: shirt; color: white; secondary_colors: blue; "
        "silhouette: oversized button-up shirt; details: long sleeves, front buttons, spread collar"
    )
    assert profile.category == "shirt"
    assert profile.budget_max == 15000.0


def test_query_preparation_canonicalizes_specific_agent_garment_type_to_catalog_category() -> None:
    profile = build_similarity_query_profile(
        SimilarSearchRequest(
            source_type="garment_photo",
            garment_profile=SimilarSearchGarmentProfile(
                garment_type="white button-up shirt",
                dominant_color="white",
                silhouette_summary="oversized shirt",
                confidence=0.92,
            ),
        )
    )

    assert profile.category == "shirt"


def test_canonicalize_garment_category_maps_common_catalog_groups() -> None:
    assert canonicalize_garment_category("button-down blouse") == "shirt"
    assert canonicalize_garment_category("long sleeve t-shirt") == "tshirt"
    assert canonicalize_garment_category("straight denim jeans") == "pants"
    assert canonicalize_garment_category("quilted jacket") == "outerwear"


def test_canonicalize_garment_category_prefers_outerwear_for_shirt_jackets() -> None:
    assert canonicalize_garment_category("quilted shirt jacket") == "outerwear"
    assert canonicalize_garment_category("oversized jacket shirt outerwear") == "outerwear"
