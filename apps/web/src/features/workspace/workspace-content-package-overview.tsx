"use client";

import { SiteButton } from "@/components/site/site-button";
import { useWorkspaceCapabilityVerdict } from "@/features/workspace/use-workspace-capability-verdict";
import { WorkspaceCapabilitySummaryPanel } from "@/features/workspace/workspace-capability-summary-panel";
import { WorkspaceLockedProductionActions } from "@/features/workspace/workspace-locked-production-actions";
import { WorkspaceActionCard } from "@/features/workspace/workspace-section-primitives";
import { WorkspaceShellState } from "@/features/workspace/workspace-shell-state";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";

export function WorkspaceContentPackageOverview() {
  const { bootstrap, error, hasCapability, isLoading, refresh } = useWorkspaceRuntime();
  const canManualExport = hasCapability("manual_export");
  const canPublish = hasCapability("marketplace_publish");
  const canImportCatalog = hasCapability("catalog_import");
  const canSyncCatalog = hasCapability("catalog_sync");
  const { publishVerdict } = useWorkspaceCapabilityVerdict({
    capabilityForAssert: "marketplace_publish",
    enabled: Boolean(bootstrap),
  });

  if (!bootstrap) {
    return <WorkspaceShellState error={error} hasBootstrap={Boolean(bootstrap)} isLoading={isLoading} onRetry={refresh} />;
  }

  const summaryItems = [
    {
      title: "ZIP и артефакты",
      body: canManualExport
        ? "Сервер уже разрешает manual export, поэтому ZIP и экспортные артефакты можно использовать как честный B2B-результат."
        : "Manual export сейчас закрыт сервером, поэтому экран не должен обещать готовую выгрузку."
    },
    {
      title: "Операционный контур",
      body: "Контент-пакет остается backend-owned: frontend только показывает доступность действий и результаты server checks."
    },
  ];

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Пакет контента</p>
        <h1 className="workspace-page-title mt-4">Контент-пакет и ручная выгрузка</h1>
        <p className="workspace-page-lead mt-4 max-w-[900px]">
          Это B2B-операционный экран. ZIP, тексты и ручная выгрузка допустимы без магазина.
          Публикация в канал, импорт и sync должны зависеть только от backend capabilities.
        </p>
      </section>

      <section className="mt-[50px] grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="grid gap-5">
          <WorkspaceCapabilitySummaryPanel
            publishVerdict={publishVerdict}
            summaryItems={summaryItems}
            title="Что уже доступно"
          />

          <WorkspaceActionCard>
            <div className="flex flex-wrap gap-3">
              <SiteButton href="/workspace/history" variant="secondary">
                Открыть историю
              </SiteButton>
              <SiteButton href="/workspace/product-card" variant="violet">
                Вернуться к карточке товара
              </SiteButton>
              <SiteButton href="/workspace/integrations" variant="secondary">
                Открыть интеграции
              </SiteButton>
              <SiteButton disabled variant="soft">
                Экспорт будет доступен после backend wiring
              </SiteButton>
            </div>
          </WorkspaceActionCard>
        </div>

        <WorkspaceLockedProductionActions
          canImportCatalog={canImportCatalog}
          canPublish={canPublish}
          canSyncCatalog={canSyncCatalog}
        />
      </section>
    </main>
  );
}
