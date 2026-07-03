"use client";

import { SiteButton } from "@/components/site/site-button";
import { WorkspaceShellState } from "@/features/workspace/workspace-shell-state";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";

export default function WorkspaceProjectsPage() {
  const { bootstrap, error, isLoading, refresh } = useWorkspaceRuntime();

  if (!bootstrap) {
    return <WorkspaceShellState error={error} hasBootstrap={Boolean(bootstrap)} isLoading={isLoading} onRetry={refresh} />;
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Проекты</p>
        <h1 className="workspace-page-title mt-4">История задач и рабочих сценариев</h1>
        <p className="workspace-page-lead mt-4 max-w-[900px]">
          Это обязательный workspace-маршрут для пользовательских и B2B-проектов. Экран опирается на backend-owned
          recent jobs и не показывает выдуманные статусы или фейковые карточки.
        </p>
      </section>

      {bootstrap.recent_jobs.length > 0 ? (
        <section className="mt-[50px] grid gap-5 lg:grid-cols-3">
          {bootstrap.recent_jobs.map((job) => (
            <article className="site-card p-7 lg:p-8" key={job.job_id}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="workspace-meta uppercase tracking-[0.12em]">{job.workflow_type}</p>
                  <h2 className="workspace-card-title mt-3">{job.title}</h2>
                </div>
                <span className="rounded-full bg-[var(--ai-soft)] px-3 py-2 text-[0.78rem] font-semibold text-[var(--ai)]">
                  {job.status}
                </span>
              </div>
              {job.summary ? <p className="workspace-body mt-4">{job.summary}</p> : null}
              <p className="workspace-meta mt-5">{job.updated_at}</p>
              <SiteButton className="mt-7" href={job.href} variant="soft">
                Открыть
              </SiteButton>
            </article>
          ))}
        </section>
      ) : (
        <section className="mt-[50px] grid gap-5 xl:grid-cols-3">
          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-card-title">Личные сценарии</h2>
            <p className="workspace-body mt-4">
              После первых backend-задач здесь появятся примерки, подборы образов и поисковые сценарии. Пока экран
              честно показывает пустое состояние.
            </p>
          </article>
          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-card-title">B2B-потоки</h2>
            <p className="workspace-body mt-4">
              Карточки товара, контент-пакеты и ручная выгрузка будут собираться здесь отдельным контуром, когда
              backend начнет отдавать unified project feed.
            </p>
          </article>
          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-card-title">Что нужно дальше</h2>
            <p className="workspace-body mt-4">
              Серверу нужно расширить recent jobs до общего project stream, чтобы этот экран стал полноценной рабочей
              лентой, а не только историей отдельных workflow.
            </p>
          </article>
        </section>
      )}

      <div className="mt-[50px] flex flex-wrap gap-3">
        <SiteButton href="/workspace/new-fitting" variant="violet">
          Новая примерка
        </SiteButton>
        <SiteButton href="/workspace/product-card" variant="secondary">
          Карточка товара
        </SiteButton>
      </div>
    </main>
  );
}
