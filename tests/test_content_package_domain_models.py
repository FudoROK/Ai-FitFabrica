from src.domain.content_package import ContentPackageOption, ContentPackageRequest


def test_content_package_request_keeps_requested_output_channels() -> None:
    request = ContentPackageRequest(
        product_card_version_id="version-1",
        package_name="marketplace-launch",
        requested_channels=["wildberries", "instagram"],
    )

    assert request.requested_channels == ["wildberries", "instagram"]


def test_content_package_option_exposes_asset_kind_and_label() -> None:
    option = ContentPackageOption(asset_kind="caption", label="Instagram caption")
    assert option.asset_kind == "caption"
