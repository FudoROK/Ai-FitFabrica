from src.adapters.database.sql.product_card_models import ProductCardJobRow, ProductCardVersionRow


def test_product_card_sql_models_define_job_and_version_tables() -> None:
    assert ProductCardJobRow.__tablename__ == "product_card_jobs"
    assert ProductCardVersionRow.__tablename__ == "product_card_versions"
