from src.adapters.database.sql.pricing_models import PricingJobRow, PricingRecommendationRow


def test_pricing_sql_models_define_job_and_recommendation_tables() -> None:
    assert PricingJobRow.__tablename__ == "pricing_jobs"
    assert PricingRecommendationRow.__tablename__ == "pricing_recommendations"
