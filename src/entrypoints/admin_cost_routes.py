"""Admin-only cost and credits baseline API routes."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.costs.credits_pricing_policy import CreditsPricingPolicy, CreditsPricingRecommendation
from src.costs.provider_price_config import COST_CONFIG_VERSION, ProviderModelPrice, list_provider_model_prices
from src.entrypoints.admin_auth import AdminActor, resolve_admin_actor
from src.settings import Settings

router = APIRouter(prefix="/api/admin/costs", tags=["admin-costs"])

_CREDIT_VALUE_KZT = Decimal("50")
_USD_TO_KZT = Decimal("500")

_BASELINE_INTERNAL_COST_USD_BY_ACTION: dict[str, tuple[str, Decimal]] = {
    "Try-On Base": ("try_on", Decimal("0.060000")),
    "Try-On With Repair": ("try_on", Decimal("0.120000")),
    "Product Card Text Only": ("product_card", Decimal("0.030000")),
    "Product Card + 1 Model Photo": ("product_card", Decimal("0.090000")),
    "Product Card + Model Photo + Quality Verification": ("product_card", Decimal("0.110000")),
    "Product Card + Content Package": ("product_card", Decimal("0.180000")),
    "Similar Search Local Catalog": ("similar_search", Decimal("0.015000")),
    "Similar Search External Connector": ("similar_search", Decimal("0.050000")),
    "Content Package Text Only": ("content_package", Decimal("0.025000")),
    "Content Package + 1 Generated Image": ("content_package", Decimal("0.075000")),
    "Content Package + 3 Generated Images": ("content_package", Decimal("0.160000")),
    "Content Package + 5 Generated Images": ("content_package", Decimal("0.250000")),
}


class AdminCostGuardrails(BaseModel):
    """Read-only safety rules for admin cost endpoints."""

    model_config = ConfigDict(extra="forbid")

    live_billing_changed: bool
    frontend_may_calculate_credits: bool
    endpoint_mutates_state: bool
    recalibration_required_after_runs: str


class AdminCostBaselineResponse(BaseModel):
    """Admin read-only cost baseline response."""

    model_config = ConfigDict(extra="forbid")

    credit_value_kzt: Decimal = Field(ge=Decimal("0"))
    usd_to_kzt: Decimal = Field(ge=Decimal("0"))
    provider_price_config_version: str
    provider_prices: list[ProviderModelPrice]
    workflow_credit_costs: dict[str, int]
    pricing_recommendations: list[CreditsPricingRecommendation]
    guardrails: AdminCostGuardrails


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""

    return request.app.state.settings


def _admin_actor(
    settings: Settings,
    authorization: str | None,
    admin_role: str | None,
    admin_id: str | None,
) -> AdminActor | JSONResponse:
    """Validate admin cost feature flag and bearer token."""

    if not bool(getattr(settings, "enable_admin_costs", False)):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "admin_costs_disabled",
                    "message": "Admin costs API is disabled.",
                }
            },
        )
    return resolve_admin_actor(
        settings=settings,
        allowed_roles={"admin", "cost_admin"},
        authorization=authorization,
        legacy_admin_role=admin_role,
        legacy_admin_id=admin_id,
    )


@router.get("/baseline", response_model=AdminCostBaselineResponse)
async def get_admin_cost_baseline(
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminCostBaselineResponse | JSONResponse:
    """Return read-only cost/pricing assumptions for admin review."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    pricing_policy = CreditsPricingPolicy(credit_value_kzt=_CREDIT_VALUE_KZT, usd_to_kzt=_USD_TO_KZT)
    return AdminCostBaselineResponse(
        credit_value_kzt=_CREDIT_VALUE_KZT,
        usd_to_kzt=_USD_TO_KZT,
        provider_price_config_version=COST_CONFIG_VERSION,
        provider_prices=list_provider_model_prices(),
        workflow_credit_costs=_workflow_credit_costs(settings),
        pricing_recommendations=[
            pricing_policy.recommend_for_action(
                product_action=product_action,
                workflow_type=workflow_type,
                internal_cost_usd_avg=internal_cost_usd,
            )
            for product_action, (workflow_type, internal_cost_usd) in _BASELINE_INTERNAL_COST_USD_BY_ACTION.items()
        ],
        guardrails=AdminCostGuardrails(
            live_billing_changed=False,
            frontend_may_calculate_credits=False,
            endpoint_mutates_state=False,
            recalibration_required_after_runs="20-50 staging/prod workflow runs",
        ),
    )


def _workflow_credit_costs(settings: Settings) -> dict[str, int]:
    """Return configured backend-owned base credit costs."""

    return {
        "try_on": int(getattr(settings, "try_on_base_credit_cost", 12)),
        "product_card": int(getattr(settings, "product_card_base_credit_cost", 18)),
        "content_package": int(getattr(settings, "content_package_base_credit_cost", 14)),
        "pricing": int(getattr(settings, "pricing_base_credit_cost", 6)),
    }
