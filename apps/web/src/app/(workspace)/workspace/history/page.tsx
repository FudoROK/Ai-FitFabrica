"use client";

import { SiteButton } from "@/components/site/site-button";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";

export default function WorkspaceHistoryPage() {
  const { bootstrap } = useWorkspaceRuntime();

  if (!bootstrap) {
    return null;
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">История</p>
        <h1 className="workspace-page-title mt-4">История личных сценариев</h1>
        <p className="workspace-page-lead mt-4 max-w-[880px]">
          Здесь собирается лента последних результатов пользователя. Экран не показывает выдуманные записи и
          опирается только на backend-owned recent jobs.
        </p>
      </section>

      {bootstrap.recent_jobs.length > 0 ? (
        <section className="mt-[50px]">
          <div className="grid gap-5 lg:grid-cols-3">
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
          </div>
        </section>
      ) : (
        <section className="mt-[50px] grid gap-5 xl:grid-cols-3">
          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-card-title">Личные результаты</h2>
            <p className="workspace-body mt-4">
              Когда сервер начнет возвращать последние задачи, здесь появятся примерки, подборы образов и поисковые
              сценарии.
            </p>
            <SiteButton className="mt-8" href="/workspace" variant="soft">
              Вернуться к кабинету
            </SiteButton>
          </article>

          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-card-title">Проекты и B2B-потоки</h2>
            <p className="workspace-body mt-4">
              Для смешанной ленты личных и бизнес-сценариев используйте раздел проектов. Он нужен для общего project
              stream, а история остается личным слоем.
            </p>
            <SiteButton className="mt-8" href="/workspace/projects" variant="soft">
              Открыть проекты
            </SiteButton>
          </article>

          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-card-title">Что нужно для полной истории</h2>
            <p className="workspace-body mt-4">
              Сервер должен расширить unified recent jobs до общего списка сценариев и проектных сущностей. До этого
              момента интерфейс не должен выдумывать карточки и статусы.
            </p>
            <SiteButton className="mt-8" href="/workspace/integrations" variant="secondary">
              Посмотреть интеграции
            </SiteButton>
          </article>
        </section>
      )}

      <section className="mt-[50px] site-card p-7 lg:p-8">
        <h2 className="workspace-section-title">Следующий шаг</h2>
        <p className="workspace-body mt-4 max-w-[820px]">
          Чтобы история перестала быть пустой, нужно завершить хотя бы одну задачу через backend workflows. После этого
          лента начнет собираться из реальных событий.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <SiteButton href="/workspace/new-fitting" variant="violet">
            Запустить примерку
          </SiteButton>
          <SiteButton href="/workspace/product-card" variant="secondary">
            Открыть карточку товара
          </SiteButton>
        </div>
      </section>
    </main>
  );
}
