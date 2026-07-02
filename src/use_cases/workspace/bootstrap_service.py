"""Backend-owned workspace bootstrap service."""

from __future__ import annotations

from src.domain.billing import BillingOwnerType
from src.domain.workspace import (
    WorkspaceBootstrapResponse,
    WorkspaceBusinessProfileSummary,
    WorkspaceCreditOwnerSummary,
    WorkspaceCreditsSummary,
    WorkspaceIntegrationSummary,
    WorkspaceQuickAction,
    WorkspaceRecentJobSummary,
    WorkspaceUserSummary,
    WorkspaceWorkflowCosts,
)
from src.use_cases.billing.service import BillingService
from src.use_cases.content_package.ports import ContentPackageRepositoryPort
from src.use_cases.product_card.ports import ProductCardRepositoryPort
from src.use_cases.try_on.ports import TryOnJobRepositoryPort
from src.use_cases.workspace.capability_service import build_workspace_capability_states, enabled_workspace_capabilities
from src.use_cases.workspace.ports import WorkspaceStateRepositoryPort


class WorkspaceBootstrapService:
    """Assemble one honest workspace bootstrap payload from backend-owned state."""

    def __init__(
        self,
        *,
        billing_service: BillingService,
        owner_id: str,
        owner_type: BillingOwnerType,
        billing_enabled: bool,
        product_card_credit_cost: int = 0,
        try_on_job_repository: TryOnJobRepositoryPort | None = None,
        workspace_state_repository: WorkspaceStateRepositoryPort | None = None,
        product_card_repository: ProductCardRepositoryPort | None = None,
        content_package_repository: ContentPackageRepositoryPort | None = None,
        default_first_name: str | None = None,
        default_full_name: str | None = None,
    ) -> None:
        """Store the backend services and workspace identity defaults."""
        self._billing_service = billing_service
        self._owner_id = owner_id
        self._owner_type = owner_type
        self._billing_enabled = billing_enabled
        self._product_card_credit_cost = product_card_credit_cost
        self._try_on_job_repository = try_on_job_repository
        self._workspace_state_repository = workspace_state_repository
        self._product_card_repository = product_card_repository
        self._content_package_repository = content_package_repository
        self._default_first_name = default_first_name
        self._default_full_name = default_full_name

    async def get_bootstrap(self) -> WorkspaceBootstrapResponse:
        """Return the unified workspace bootstrap response."""
        balance = await self._billing_service.get_account_balance(
            owner_id=self._owner_id,
            owner_type=self._owner_type,
        )
        business_profile = await self._build_business_profile()
        integrations = await self._build_integrations()
        capabilities = self._resolve_capabilities(
            business_profile=business_profile,
            integrations=integrations,
        )
        recent_jobs = await self._build_recent_jobs()

        return WorkspaceBootstrapResponse(
            user=WorkspaceUserSummary(
                first_name=self._default_first_name,
                full_name=self._default_full_name,
            ),
            credit_owner=WorkspaceCreditOwnerSummary(
                owner_id=self._owner_id,
                owner_type=self._owner_type,
            ),
            credits=WorkspaceCreditsSummary(
                balance=balance.available_credits,
                low_balance_threshold=12,
                billing_enabled=self._billing_enabled,
            ),
            workflow_costs=WorkspaceWorkflowCosts(product_card=self._product_card_credit_cost),
            business_profile=business_profile,
            integrations=integrations,
            capabilities=capabilities,
            quick_actions=self._build_quick_actions(capabilities=capabilities),
            recent_jobs=recent_jobs,
        )

    def _resolve_capabilities(
        self,
        *,
        business_profile: WorkspaceBusinessProfileSummary,
        integrations: WorkspaceIntegrationSummary,
    ) -> list[str]:
        """Return the currently available workspace capabilities."""
        capability_states = build_workspace_capability_states(
            business_profile=business_profile,
            integrations=integrations,
        )
        return enabled_workspace_capabilities(capability_states=capability_states)

    def _build_quick_actions(self, *, capabilities: list[str]) -> list[WorkspaceQuickAction]:
        """Return dashboard quick actions derived from explicit capabilities."""
        capability_set = set(capabilities)
        return [
            self._action(
                action_id="try-on",
                label="Новая примерка",
                description="Загрузите фото человека и одежды, чтобы запустить примерку прямо в рабочей зоне.",
                href="/workspace/new-fitting",
                capability="try_on_create",
                enabled="try_on_create" in capability_set,
                disabled_reason="Пополните баланс или дождитесь повторной активации примерки.",
            ),
            self._action(
                action_id="outfit-builder",
                label="Подбор образа",
                description="Соберите образ и подготовьте рекомендации по сезону, случаю и бюджету.",
                href="/workspace/outfit-builder",
                capability="outfit_builder_create",
                enabled="outfit_builder_create" in capability_set,
                disabled_reason="Функция временно недоступна для этого аккаунта.",
            ),
            self._action(
                action_id="similar",
                label="Найти похожее",
                description="Ищите похожие вещи, альтернативы дешевле и будущие конкурентные снимки.",
                href="/workspace/similar-search",
                capability="similar_search_create",
                enabled="similar_search_create" in capability_set,
                disabled_reason="Функция временно недоступна для этого аккаунта.",
            ),
            self._action(
                action_id="product-card",
                label="Карточка товара",
                description="Создавайте карточки товара и контент-пакеты даже без подключенного магазина.",
                href="/workspace/product-card",
                capability="product_card_create",
                enabled="product_card_create" in capability_set,
                disabled_reason="Функция временно недоступна для этого аккаунта.",
            ),
        ]

    def _action(
        self,
        *,
        action_id: str,
        label: str,
        description: str,
        href: str,
        capability: str,
        enabled: bool,
        disabled_reason: str,
    ) -> WorkspaceQuickAction:
        """Build one quick action row."""
        return WorkspaceQuickAction(
            id=action_id,
            label=label,
            description=description,
            href=href,
            capability=capability,
            enabled=enabled,
            disabled_reason=None if enabled else disabled_reason,
        )

    async def _build_recent_jobs(self) -> list[WorkspaceRecentJobSummary]:
        """Return compact recent jobs for dashboard and history routes."""
        recent_jobs: list[WorkspaceRecentJobSummary] = []

        if self._try_on_job_repository is not None:
            jobs = await self._try_on_job_repository.list_recent(limit=6)
            for job in jobs:
                latest_message = job.status_history[-1].message if job.status_history else None
                recent_jobs.append(
                    WorkspaceRecentJobSummary(
                        job_id=job.job_id,
                        workflow_type=str(job.workflow_type),
                        title=f"Примерка {job.job_id}",
                        status=str(job.status),
                        href=f"/workspace/try-on/result?job_id={job.job_id}",
                        updated_at=job.updated_at.isoformat(),
                        summary=job.result.stylist_note if job.result is not None else latest_message,
                    )
                )

        if self._workspace_state_repository is not None:
            requests = await self._workspace_state_repository.list_outfit_builder_requests(owner_id=self._owner_id)
            for request in requests:
                updated_at = request.updated_at or request.created_at
                recent_jobs.append(
                    WorkspaceRecentJobSummary(
                        job_id=request.request_id,
                        workflow_type=request.workflow,
                        title=f"Подбор образа {request.request_id}",
                        status="completed",
                        href="/workspace/outfit-builder",
                        updated_at=updated_at.isoformat() if updated_at is not None else "",
                        summary=request.message,
                    )
                )

        if self._product_card_repository is not None:
            jobs = await self._product_card_repository.list_recent(limit=6)
            for job in jobs:
                version = await self._product_card_repository.get_latest_version(job.job_id)
                recent_jobs.append(
                    WorkspaceRecentJobSummary(
                        job_id=job.job_id,
                        workflow_type="product_card",
                        title=f"Карточка товара {job.job_id}",
                        status=job.status,
                        href="/workspace/product-card",
                        updated_at=job.updated_at.isoformat(),
                        summary=version.title if version is not None else job.title_hint,
                    )
                )

        if self._content_package_repository is not None:
            jobs = await self._content_package_repository.list_recent(limit=6)
            for job in jobs:
                version = await self._content_package_repository.get_latest_version(job.job_id)
                recent_jobs.append(
                    WorkspaceRecentJobSummary(
                        job_id=job.job_id,
                        workflow_type="content_package",
                        title=f"Контент-пакет {job.job_id}",
                        status=job.status,
                        href="/workspace/content-package",
                        updated_at=job.updated_at.isoformat(),
                        summary=version.package_name if version is not None else job.package_name,
                    )
                )

        recent_jobs.sort(key=lambda item: item.updated_at, reverse=True)
        return recent_jobs[:6]

    async def _build_business_profile(self) -> WorkspaceBusinessProfileSummary:
        """Return persisted business-profile summary for the current owner."""
        if self._workspace_state_repository is None:
            return WorkspaceBusinessProfileSummary(
                exists=False,
                display_name=None,
                channels=[],
            )

        profile = await self._workspace_state_repository.get_business_profile(owner_id=self._owner_id)
        if profile is None:
            return WorkspaceBusinessProfileSummary(
                exists=False,
                display_name=None,
                channels=[],
            )

        return WorkspaceBusinessProfileSummary(
            exists=True,
            display_name=profile.display_name,
            channels=list(profile.channels),
        )

    async def _build_integrations(self) -> WorkspaceIntegrationSummary:
        """Return persisted integrations summary for the current owner."""
        if self._workspace_state_repository is None:
            return WorkspaceIntegrationSummary(
                has_connected_store=False,
                connected_channels=[],
            )

        integrations = await self._workspace_state_repository.get_integrations(owner_id=self._owner_id)
        return WorkspaceIntegrationSummary(
            has_connected_store=integrations.has_connected_store or bool(integrations.connected_channels),
            connected_channels=list(integrations.connected_channels),
        )


__all__ = ["WorkspaceBootstrapService"]
