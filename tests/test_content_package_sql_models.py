from src.adapters.database.sql.content_package_models import ContentPackageJobRow, ContentPackageVersionRow


def test_content_package_sql_models_define_job_and_version_tables() -> None:
    assert ContentPackageJobRow.__tablename__ == "content_package_jobs"
    assert ContentPackageVersionRow.__tablename__ == "content_package_versions"
