"use client";

import { ProductCardWorkflow } from "@/features/workspace/product-card-workflow";
import { WorkspaceLockedProductionActions } from "@/features/workspace/workspace-locked-production-actions";
import { WorkspaceShellState } from "@/features/workspace/workspace-shell-state";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";

export function WorkspaceProductCardOverview() {
  const { bootstrap, error, hasCapability, isLoading, refresh } = useWorkspaceRuntime();
  const hasBusinessTemplates = hasCapability("business_templates");
  const canPublish = hasCapability("marketplace_publish");
  const canImportCatalog = hasCapability("catalog_import");
  const canSyncCatalog = hasCapability("catalog_sync");

  if (!bootstrap) {
    return <WorkspaceShellState error={error} hasBootstrap={Boolean(bootstrap)} isLoading={isLoading} onRetry={refresh} />;
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Карточка товара</p>
        <h1 className="workspace-page-title mt-4">Создание карточки через backend workflow</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Загрузите фото и параметры. Backend создаст задачу, сохранит исходник, подготовит карточку и вернёт результат.
        </p>
        <p className="workspace-meta mt-4">
          Брендовые шаблоны: {hasBusinessTemplates ? "доступны" : "нужен business profile"}.
          Production actions: {canPublish && canImportCatalog && canSyncCatalog ? "capabilities открыты, pipelines всё ещё заблокированы" : "заблокированы"}.
        </p>
      </section>
      <section className="mt-[50px] grid gap-5">
        <ProductCardWorkflow />
        <WorkspaceLockedProductionActions
          canImportCatalog={canImportCatalog}
          canPublish={canPublish}
          canSyncCatalog={canSyncCatalog}
        />
      </section>
    </main>
  );
}
