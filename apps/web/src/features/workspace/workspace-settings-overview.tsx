"use client";

import { SiteButton } from "@/components/site/site-button";
import { useWorkspaceCapabilityVerdict } from "@/features/workspace/use-workspace-capability-verdict";
import { WorkspaceActionCard, WorkspaceSectionCard } from "@/features/workspace/workspace-section-primitives";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import { WorkspaceShellState } from "@/features/workspace/workspace-shell-state";

export function WorkspaceSettingsOverview() {
  const { bootstrap, error, isLoading, refresh } = useWorkspaceRuntime();
  const { matrix } = useWorkspaceCapabilityVerdict({ enabled: Boolean(bootstrap) });

  if (isLoading || error || !bootstrap) {
    return (
      <WorkspaceShellState
        error={error}
        hasBootstrap={Boolean(bootstrap)}
        isLoading={isLoading}
        onRetry={refresh}
      />
    );
  }

  const publishGate = matrix?.capability_states.find((item) => item.capability === "marketplace_publish") ?? null;

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Настройки</p>
        <h1 className="workspace-page-title mt-4">Профили, интеграции и параметры workspace</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Этот раздел показывает только актуальное backend-owned состояние. Клиент не принимает продуктовые решения и не считает кредиты, а отображает живые summary и реальные переходы в связанные разделы.
        </p>
      </section>

      <section className="mt-[50px] grid gap-5 xl:grid-cols-2">
        <WorkspaceSectionCard title="Личный контур">
          <p className="workspace-body mt-4">
            Стиль-профиль остается отдельным тонким клиентским экраном. Он нужен для размеров, предпочтений и ограничений, но не должен содержать credits logic или orchestration.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <SiteButton className="mt-0" href="/workspace/style-profile" variant="soft">
              Открыть стиль-профиль
            </SiteButton>
            <SiteButton href="/workspace" variant="secondary">
              Вернуться в workspace
            </SiteButton>
          </div>
        </WorkspaceSectionCard>

        <WorkspaceSectionCard title="Бизнес-контур">
          <p className="workspace-body mt-4">
            {bootstrap.business_profile.exists
              ? `Профиль активен: ${bootstrap.business_profile.display_name ?? "название еще не задано"}.`
              : "Бизнес-профиль еще не сохранен. Его нужно заполнить до реальной брендовой настройки и публикации."}
          </p>
          <p className="workspace-body mt-4">
            Каналы профиля: {bootstrap.business_profile.channels.length > 0 ? bootstrap.business_profile.channels.join(", ") : "еще не выбраны"}.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <SiteButton href="/workspace/business-profile" variant="violet">
              Бизнес-профиль
            </SiteButton>
            <SiteButton href="/workspace/integrations" variant="secondary">
              Интеграции
            </SiteButton>
          </div>
        </WorkspaceSectionCard>
      </section>

      <section className="mt-[50px] grid gap-5 xl:grid-cols-3">
        <WorkspaceActionCard>
          <h2 className="workspace-card-title">Кредиты</h2>
          <p className="workspace-body mt-4">
            Текущий баланс: {bootstrap.credits.balance}. Источник данных остается backend-owned и не пересчитывается на клиенте.
          </p>
          <p className="workspace-body mt-4">Billing: {bootstrap.credits.billing_enabled ? "включен" : "выключен"}.</p>
          <SiteButton className="mt-8" href="/workspace/credits" variant="soft">
            Открыть кредиты
          </SiteButton>
        </WorkspaceActionCard>

        <WorkspaceActionCard>
          <h2 className="workspace-card-title">Магазин и каналы</h2>
          <p className="workspace-body mt-4">
            {bootstrap.integrations.has_connected_store
              ? "Подключенный магазин найден. Можно двигаться к publish, import и sync поверх backend-проверок."
              : "Подключенного магазина пока нет. Автопубликация не должна притворяться доступной."}
          </p>
          <p className="workspace-body mt-4">
            Подключенные каналы: {bootstrap.integrations.connected_channels.length > 0 ? bootstrap.integrations.connected_channels.join(", ") : "еще не подключены"}.
          </p>
          <SiteButton className="mt-8" href="/workspace/integrations" variant="soft">
            Открыть интеграции
          </SiteButton>
        </WorkspaceActionCard>

        <WorkspaceActionCard>
          <h2 className="workspace-card-title">Готовность</h2>
          <p className="workspace-body mt-4">
            Экран настроек теперь собран на реальном runtime state: `business_profile`, `integrations`, `credits`.
          </p>
          <p className="workspace-body mt-4">
            Следующий шаг по этому контуру: развести реальные channel settings и backend gates для publish/import/sync.
          </p>
          {publishGate ? (
            <p className="workspace-body mt-4">
              Server verdict по publish: {publishGate.enabled ? "доступно" : publishGate.disabled_reason ?? "закрыто"}.
            </p>
          ) : null}
          <SiteButton className="mt-8" onClick={() => void refresh()} variant="ghost">
            Обновить состояние
          </SiteButton>
        </WorkspaceActionCard>
      </section>
    </main>
  );
}
