"use client";

import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";

type WorkspaceLockedProductionActionsProps = {
  canImportCatalog: boolean;
  canPublish: boolean;
  canSyncCatalog: boolean;
};

export function WorkspaceLockedProductionActions({
  canImportCatalog,
  canPublish,
  canSyncCatalog,
}: WorkspaceLockedProductionActionsProps) {
  const { bootstrap } = useWorkspaceRuntime();

  if (!bootstrap) {
    return null;
  }

  return (
    <section className="site-card p-7 lg:p-8">
      <p className="eyebrow">Публикация и каталоги</p>
      <h2 className="workspace-section-title mt-4">Production pipelines пока заблокированы</h2>
      <p className="workspace-body mt-4">
        Создание и сохранение карточки работает через backend. Publish, import и sync не запускаются,
        пока не подключены реальные pipeline и магазин.
      </p>
      <div className="mt-6 grid gap-3">
        {[
          { enabled: canPublish, label: "Публикация в магазин" },
          { enabled: canImportCatalog, label: "Импорт каталога" },
          { enabled: canSyncCatalog, label: "Синхронизация каталога" },
        ].map((action) => (
          <button
            className="min-h-[52px] cursor-not-allowed rounded-full border border-[var(--border)] bg-[var(--surface-alt)] px-6 text-left text-sm font-semibold text-[var(--text-muted)]"
            disabled
            key={action.label}
            type="button"
          >
            {action.label}: {action.enabled ? "capability открыта, pipeline не подключён" : "capability закрыта"}
          </button>
        ))}
      </div>
      <p className="workspace-meta mt-5">
        Магазин: {bootstrap.integrations.has_connected_store ? "подключён" : "не подключён"}.
      </p>
    </section>
  );
}
