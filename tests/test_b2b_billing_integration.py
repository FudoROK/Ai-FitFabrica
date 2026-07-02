from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.adapters.billing.in_memory_repository import InMemoryBillingRepository
from src.domain.billing import BillingOwnerType
from src.domain.content_package import ContentPackageOption, ContentPackageRequest
from src.domain.product_card import ProductCardDraft, ProductCardRequest
from src.domain.pricing import PricingComparable, PricingRequest
from src.use_cases.billing.policy import BillingPolicyResolver
from src.use_cases.billing.service import BillingService
from src.use_cases.content_package.workflow_service import ContentPackageWorkflowService
from src.use_cases.pricing.workflow_service import PricingWorkflowService
from src.use_cases.product_card.workflow_service import ProductCardSourceFile, ProductCardWorkflowService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_product_card_records_charge_through_billing_core() -> None:
    class _FileStorageStub:
        async def store_many(self, *, source_files):
            return [f"assets/{source_files[0].filename}"]

    class _RepositoryStub:
        async def create_job(self, *, request, asset_keys, now):
            from src.domain.product_card import ProductCardJobRecord

            return ProductCardJobRecord(
                job_id="product_card_1",
                status="accepted",
                target_channel=request.target_channel,
                brand_tone=request.brand_tone,
                title_hint=request.title_hint,
                asset_keys=asset_keys,
                created_at=now,
                updated_at=now,
            )

        async def save_generated_version(self, *, job_id, draft, now):
            from src.domain.product_card import ProductCardVersionRecord

            return ProductCardVersionRecord(
                version_id=f"{job_id}_v1",
                job_id=job_id,
                title=draft.title,
                description=draft.description,
                bullet_points=draft.bullet_points,
                attributes=draft.attributes,
                created_at=now,
            )

        async def save_garment_analysis(self, analysis):
            return analysis

        async def mark_completed(self, job_id: str, *, now):
            from src.domain.product_card import ProductCardJobRecord

            return ProductCardJobRecord(
                job_id=job_id,
                status="completed",
                target_channel="wb",
                brand_tone="minimal",
                title_hint="Dress",
                asset_keys=["assets/source.png"],
                created_at=now,
                updated_at=now,
            )

        async def get_job(self, job_id: str):
            return None

        async def get_latest_version(self, job_id: str):
            return None

    class _GenerationStub:
        async def generate(self, *, request, garment_analysis):
            return ProductCardDraft(
                title=request.title_hint or "Generated",
                description="Generated product card",
                bullet_points=["one"],
                attributes={"category": "dress"},
            )

    class _GarmentAnalysisStub:
        async def analyze(self, *, job_id, asset_keys):
            from src.domain.product_card import ProductCardGarmentAnalysis

            return ProductCardGarmentAnalysis(
                job_id=job_id,
                invocation_id="garment-invocation-1",
                prompt_version="garment_identity.v1",
                contract_version="garment_identity.contract.v1",
                garment_type="dress",
                dominant_color="blue",
                silhouette_summary="Midi dress.",
                confidence=0.95,
                uncertainty_level="low",
            )

    billing_repository = InMemoryBillingRepository()
    await billing_repository.ensure_account(owner_id="business-1", owner_type="business", initial_credits=100)
    billing_service = BillingService(
        repository=billing_repository,
        policy_resolver=BillingPolicyResolver(workflow_base_costs={"product_card": 18}),
    )
    service = ProductCardWorkflowService(
        file_storage=_FileStorageStub(),
        repository=_RepositoryStub(),
        garment_identity_analyzer=_GarmentAnalysisStub(),
        generation_adapter=_GenerationStub(),
        clock=_utc_now,
        billing_service=billing_service,
        billing_owner_id="business-1",
        billing_owner_type=BillingOwnerType.BUSINESS,
    )

    result = await service.create_product_card(
        request=ProductCardRequest(title_hint="Dress", target_channel="wb", brand_tone="minimal"),
        source_files=[ProductCardSourceFile(filename="source.png", content_type="image/png", payload=b"img")],
    )

    assert result.ledger_event is not None
    assert result.ledger_event.workflow_type == "product_card"


@pytest.mark.asyncio
async def test_content_package_and_pricing_record_charges() -> None:
    class _ContentRepositoryStub:
        async def create_job(self, *, request, now):
            from src.domain.content_package import ContentPackageJobRecord

            return ContentPackageJobRecord(
                job_id="content_package_1",
                product_card_version_id=request.product_card_version_id,
                package_name=request.package_name,
                status="accepted",
                requested_channels=list(request.requested_channels),
                created_at=now,
                updated_at=now,
            )

        async def save_package_version(self, *, job_id, package_name, assets, artifact_keys, now):
            from src.domain.content_package import ContentPackageVersionRecord

            return ContentPackageVersionRecord(
                version_id=f"{job_id}_v1",
                job_id=job_id,
                package_name=package_name,
                assets=assets,
                created_at=now,
            )

        async def mark_completed(self, job_id: str, *, now):
            from src.domain.content_package import ContentPackageJobRecord

            return ContentPackageJobRecord(
                job_id=job_id,
                product_card_version_id="version-1",
                package_name="insta-pack",
                status="completed",
                requested_channels=["instagram"],
                created_at=now,
                updated_at=now,
            )

        async def get_job(self, job_id: str):
            return None

        async def get_latest_version(self, job_id: str):
            return None

    class _ArtifactStorageStub:
        async def store_generated_assets(self, *, job_id, assets):
            return [f"{job_id}/{index}" for index, _item in enumerate(assets, start=1)]

    class _ContentGenerationStub:
        async def generate(self, *, request):
            return [ContentPackageOption(asset_kind="caption", label="IG caption")]

    class _PricingRepositoryStub:
        async def create_job(self, *, request, now):
            from src.domain.pricing import PricingJobRecord

            return PricingJobRecord(
                job_id="pricing_1",
                product_id=request.product_id,
                target_currency=request.target_currency,
                desired_margin_percent=request.desired_margin_percent,
                status="accepted",
                created_at=now,
                updated_at=now,
            )

        async def save_recommendation(self, *, job_id, recommendation, now):
            from src.domain.pricing import PricingRecommendationRecord

            return PricingRecommendationRecord(
                recommendation_id=f"{job_id}_v1",
                job_id=job_id,
                recommendation=recommendation,
                created_at=now,
            )

        async def mark_completed(self, job_id: str, *, now):
            from src.domain.pricing import PricingJobRecord

            return PricingJobRecord(
                job_id=job_id,
                product_id="product-1",
                target_currency="RUB",
                desired_margin_percent=30.0,
                status="completed",
                created_at=now,
                updated_at=now,
            )

        async def get_job(self, job_id: str):
            return None

        async def get_latest_recommendation(self, job_id: str):
            return None

    class _ComparisonSourceStub:
        async def list_comparables(self, brief):
            return [
                PricingComparable(source_id="offer-1", price_amount=4000.0, currency="RUB"),
                PricingComparable(source_id="offer-2", price_amount=5000.0, currency="RUB"),
            ]

    billing_repository = InMemoryBillingRepository()
    await billing_repository.ensure_account(owner_id="business-1", owner_type="business", initial_credits=100)
    billing_service = BillingService(
        repository=billing_repository,
        policy_resolver=BillingPolicyResolver(workflow_base_costs={"content_package": 14, "pricing": 6}),
    )

    content_service = ContentPackageWorkflowService(
        repository=_ContentRepositoryStub(),
        artifact_storage=_ArtifactStorageStub(),
        generation_adapter=_ContentGenerationStub(),
        clock=_utc_now,
        billing_service=billing_service,
        billing_owner_id="business-1",
        billing_owner_type=BillingOwnerType.BUSINESS,
    )
    pricing_service = PricingWorkflowService(
        repository=_PricingRepositoryStub(),
        comparison_source=_ComparisonSourceStub(),
        clock=_utc_now,
        billing_service=billing_service,
        billing_owner_id="business-1",
        billing_owner_type=BillingOwnerType.BUSINESS,
    )

    content_result = await content_service.create_content_package(
        request=ContentPackageRequest(
            product_card_version_id="version-1",
            package_name="insta-pack",
            requested_channels=["instagram"],
        )
    )
    pricing_result = await pricing_service.create_pricing_recommendation(
        request=PricingRequest(product_id="product-1", target_currency="RUB", desired_margin_percent=30.0)
    )

    assert content_result.ledger_event is not None
    assert content_result.ledger_event.workflow_type == "content_package"
    assert pricing_result.ledger_event is not None
    assert pricing_result.ledger_event.workflow_type == "pricing"
