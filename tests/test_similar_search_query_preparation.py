from __future__ import annotations

from src.domain.similar_search import SimilarSearchRequest
from src.use_cases.similar_search.query_preparation import build_similarity_query_profile


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
