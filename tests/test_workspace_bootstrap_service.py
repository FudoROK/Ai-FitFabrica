from __future__ import annotations

from datetime import datetime, timezone

import asyncio

from src.domain.billing import BillingOwnerType, CreditAccount
from src.domain.content_package import ContentPackageJobRecord, ContentPackageOption, ContentPackageVersionRecord
from src.domain.product_card import ProductCardJobRecord, ProductCardVersionRecord
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnJob,
    TryOnJobStatus,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnUploadRole,
    TryOnWorkflowType,
)
from src.domain.workspace_state import (
    WorkspaceBusinessProfileState,
    WorkspaceIntegrationState,
    WorkspaceOutfitBuilderRequestState,
)
from src.use_cases.workspace.bootstrap_service import WorkspaceBootstrapService


class _BillingServiceStub:
    async def get_account_balance(self, *, owner_id: str, owner_type: BillingOwnerType) -> CreditAccount:
        return CreditAccount(
            owner_id=owner_id,
            owner_type=owner_type,
            available_credits=120,
            reserved_credits=0,
        )


class _TryOnRepositoryStub:
    async def list_recent(self, *, limit: int) -> list[TryOnJob]:
        assert limit == 6
        now = datetime.now(timezone.utc)
        return [
            TryOnJob(
                job_id="try_on_001",
                workflow_type=TryOnWorkflowType.TRY_ON,
                generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
                status=TryOnJobStatus.COMPLETED,
                created_at=now,
                updated_at=now,
                input_metadata=[
                    TryOnInputMetadata(
                        role=TryOnUploadRole.HUMAN_PHOTO,
                        filename="human.png",
                        content_type="image/png",
                        size_bytes=128,
                        sha256="a" * 64,
                    )
                ],
                result=TryOnResult(
                    job_id="try_on_001",
                    workflow_type=TryOnWorkflowType.TRY_ON,
                    result_image=TryOnResultImage(
                        kind="sandbox_placeholder",
                        url="/images/shared/try-on-sandbox-result.webp",
                        alt="Sandbox result",
                    ),
                    quality_report=TryOnQualityReport(
                        verdict="pass",
                        confidence=0.9,
                        checks=[],
                        limitations=[],
                    ),
                    stylist_note="Готовая примерка без ошибок.",
                    input_metadata=[],
                    completed_at=now,
                ),
            )
        ]


class _WorkspaceStateRepositoryStub:
    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        assert owner_id == "public-person"
        return WorkspaceBusinessProfileState(
            owner_id=owner_id,
            display_name="FitFabrica Studio",
            channels=["instagram", "wildberries"],
        )

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        assert owner_id == "public-person"
        return WorkspaceIntegrationState(
            owner_id=owner_id,
            connected_channels=["wildberries"],
        )

    async def list_outfit_builder_requests(self, *, owner_id: str) -> list[WorkspaceOutfitBuilderRequestState]:
        assert owner_id == "public-person"
        now = datetime.now(timezone.utc)
        return [
            WorkspaceOutfitBuilderRequestState(
                owner_id=owner_id,
                request_id="outfit_req_001",
                workflow="outfit_builder",
                status="accepted",
                occasion="office",
                budget="150",
                base_item="black blazer",
                message="Outfit-builder request accepted. Recommendation pipeline is not wired yet.",
                created_at=now,
                updated_at=now,
            )
        ]


class _ProductCardRepositoryStub:
    async def list_recent(self, *, limit: int) -> list[ProductCardJobRecord]:
        assert limit == 6
        now = datetime.now(timezone.utc)
        return [
            ProductCardJobRecord(
                job_id="product_card_001",
                status="completed",
                category="shirt",
                target_channel="wildberries",
                brand_tone="premium",
                title_hint="linen shirt",
                asset_keys=["tenant/product-card/source-1.png"],
                created_at=now,
                updated_at=now,
            )
        ]

    async def get_latest_version(self, job_id: str) -> ProductCardVersionRecord | None:
        now = datetime.now(timezone.utc)
        return ProductCardVersionRecord(
            version_id=f"{job_id}_v1",
            job_id=job_id,
            title="Premium linen shirt card",
            description="Structured product card ready for marketplace publishing.",
            bullet_points=["Natural linen", "Relaxed fit"],
            attributes={"season": "summer"},
            created_at=now,
        )


class _ContentPackageRepositoryStub:
    async def list_recent(self, *, limit: int) -> list[ContentPackageJobRecord]:
        assert limit == 6
        now = datetime.now(timezone.utc)
        return [
            ContentPackageJobRecord(
                job_id="content_package_001",
                product_card_version_id="product_card_001_v1",
                package_name="launch capsule",
                status="completed",
                requested_channels=["instagram", "wildberries"],
                created_at=now,
                updated_at=now,
            )
        ]

    async def get_latest_version(self, job_id: str) -> ContentPackageVersionRecord | None:
        now = datetime.now(timezone.utc)
        return ContentPackageVersionRecord(
            version_id=f"{job_id}_v1",
            job_id=job_id,
            package_name="launch capsule",
            assets=[
                ContentPackageOption(asset_kind="caption", label="Instagram caption"),
                ContentPackageOption(asset_kind="listing", label="Marketplace listing"),
            ],
            created_at=now,
        )


def test_workspace_bootstrap_service_exposes_recent_try_on_jobs() -> None:
    service = WorkspaceBootstrapService(
        billing_service=_BillingServiceStub(),
        owner_id="public-person",
        owner_type=BillingOwnerType.PERSON,
        billing_enabled=False,
        product_card_credit_cost=18,
        try_on_job_repository=_TryOnRepositoryStub(),
        default_first_name="Гость",
        default_full_name="Гость FitFabrica",
    )

    result = asyncio.run(service.get_bootstrap())

    assert result.credits.balance == 120
    assert result.workflow_costs.product_card == 18
    assert len(result.recent_jobs) == 1
    assert result.recent_jobs[0].job_id == "try_on_001"
    assert result.recent_jobs[0].workflow_type == "try_on"
    assert result.recent_jobs[0].href == "/workspace/try-on/result?job_id=try_on_001"
    assert result.recent_jobs[0].summary == "Готовая примерка без ошибок."


def test_workspace_bootstrap_service_reads_business_profile_and_integrations_from_repository() -> None:
    service = WorkspaceBootstrapService(
        billing_service=_BillingServiceStub(),
        owner_id="public-person",
        owner_type=BillingOwnerType.PERSON,
        billing_enabled=False,
        try_on_job_repository=_TryOnRepositoryStub(),
        workspace_state_repository=_WorkspaceStateRepositoryStub(),
        default_first_name="Гость",
        default_full_name="Гость FitFabrica",
    )

    result = asyncio.run(service.get_bootstrap())

    assert result.business_profile.exists is True
    assert result.business_profile.display_name == "FitFabrica Studio"
    assert result.business_profile.channels == ["instagram", "wildberries"]
    assert result.integrations.has_connected_store is True
    assert result.integrations.connected_channels == ["wildberries"]
    assert "business_templates" in result.capabilities
    assert "marketplace_publish" in result.capabilities
    assert "catalog_import" in result.capabilities
    assert "catalog_sync" in result.capabilities


def test_workspace_bootstrap_service_includes_recent_outfit_builder_requests() -> None:
    service = WorkspaceBootstrapService(
        billing_service=_BillingServiceStub(),
        owner_id="public-person",
        owner_type=BillingOwnerType.PERSON,
        billing_enabled=False,
        try_on_job_repository=_TryOnRepositoryStub(),
        workspace_state_repository=_WorkspaceStateRepositoryStub(),
        product_card_repository=_ProductCardRepositoryStub(),
        content_package_repository=_ContentPackageRepositoryStub(),
    )

    result = asyncio.run(service.get_bootstrap())

    assert len(result.recent_jobs) == 4
    by_id = {job.job_id: job for job in result.recent_jobs}
    assert by_id["outfit_req_001"].workflow_type == "outfit_builder"
    assert by_id["outfit_req_001"].href == "/workspace/outfit-builder"
    assert by_id["outfit_req_001"].summary == "Outfit-builder request accepted. Recommendation pipeline is not wired yet."
    assert by_id["try_on_001"].workflow_type == "try_on"
    assert by_id["product_card_001"].workflow_type == "product_card"
    assert by_id["product_card_001"].href == "/workspace/product-card"
    assert by_id["product_card_001"].summary == "Premium linen shirt card"
    assert by_id["content_package_001"].workflow_type == "content_package"
    assert by_id["content_package_001"].href == "/workspace/content-package"
    assert by_id["content_package_001"].summary == "launch capsule"


class _WorkspaceStateWithoutStoreStub:
    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        assert owner_id == "public-person"
        return WorkspaceBusinessProfileState(
            owner_id=owner_id,
            display_name="FitFabrica Studio",
            channels=["instagram"],
        )

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        assert owner_id == "public-person"
        return WorkspaceIntegrationState(
            owner_id=owner_id,
            connected_channels=[],
            has_connected_store=False,
        )

    async def list_outfit_builder_requests(self, *, owner_id: str) -> list[WorkspaceOutfitBuilderRequestState]:
        assert owner_id == "public-person"
        return []


def test_workspace_bootstrap_service_keeps_publish_capabilities_locked_without_store() -> None:
    service = WorkspaceBootstrapService(
        billing_service=_BillingServiceStub(),
        owner_id="public-person",
        owner_type=BillingOwnerType.PERSON,
        billing_enabled=False,
        workspace_state_repository=_WorkspaceStateWithoutStoreStub(),
    )

    result = asyncio.run(service.get_bootstrap())

    assert "business_templates" in result.capabilities
    assert "marketplace_publish" not in result.capabilities
    assert "catalog_import" not in result.capabilities
    assert "catalog_sync" not in result.capabilities
