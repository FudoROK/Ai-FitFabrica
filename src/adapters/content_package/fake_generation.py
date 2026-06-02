"""Deterministic fake content-package generation adapter."""

from __future__ import annotations

from src.domain.content_package import ContentPackageOption, ContentPackageRequest
from src.use_cases.content_package.ports import ContentPackageGenerationPort


class FakeContentPackageGenerationAdapter(ContentPackageGenerationPort):
    """Return a deterministic content-package asset list without calling real AI."""

    async def generate(self, *, request: ContentPackageRequest) -> list[ContentPackageOption]:
        """Build a stable content-package asset list from request metadata."""
        requested = request.requested_channels or ["default"]
        assets = [
            ContentPackageOption(asset_kind="summary", label=f"{request.package_name} summary"),
        ]
        assets.extend(
            ContentPackageOption(asset_kind="channel_export", label=f"{channel} export")
            for channel in requested
        )
        return assets
