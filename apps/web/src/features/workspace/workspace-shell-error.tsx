import { SiteButton } from "@/components/site/site-button";

export function WorkspaceShellError({
  error,
  onRetry
}: {
  error: string;
  onRetry: () => Promise<void>;
}) {
  return (
    <div className="px-6 py-8 lg:px-8 lg:py-10">
      <div className="site-card p-8 lg:p-10">
        <p className="eyebrow">Workspace</p>
        <h1 className="workspace-page-title mt-4">Не удалось загрузить рабочую зону</h1>
        <p className="workspace-page-lead mt-4 max-w-[780px]">
          Сервер не вернул состояние кабинета. Повторите загрузку, чтобы восстановить дашборд, боковую навигацию и доступные возможности.
        </p>
        <p className="workspace-meta mt-5 rounded-[1.35rem] bg-[var(--warning-soft)] px-5 py-4 text-[var(--warning)]">
          {error}
        </p>
        <SiteButton className="mt-8" onClick={() => void onRetry()} variant="soft">
          Повторить
        </SiteButton>
      </div>
    </div>
  );
}
