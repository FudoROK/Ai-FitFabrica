"use client";

import { SiteButton } from "@/components/site/site-button";
import { WorkspaceCapabilityCta } from "@/features/workspace/workspace-capability-cta";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";

function WorkspaceCreditsCard() {
  const { bootstrap } = useWorkspaceRuntime();

  if (!bootstrap) {
    return null;
  }

  const threshold = bootstrap.credits.low_balance_threshold;
  const isLowBalance = threshold !== null && bootstrap.credits.balance <= threshold;

  return (
    <article className="site-card p-7 lg:p-8">
      <p className="eyebrow">Баланс кредитов</p>
      <div className="mt-4 flex flex-wrap items-end justify-between gap-5">
        <div>
          <strong className="workspace-kpi block">{bootstrap.credits.balance}</strong>
          <p className="workspace-meta mt-3">
            {bootstrap.credits.billing_enabled
              ? "Списания и возвраты считает сервер. Интерфейс только показывает текущее состояние баланса."
              : "Сейчас списания не активны, поэтому баланс остается системным индикатором состояния среды."}
          </p>
        </div>
        <SiteButton href="/workspace/credits" variant="soft">
          Открыть кредиты
        </SiteButton>
      </div>
      {bootstrap.credits.billing_enabled && isLowBalance ? (
        <p className="workspace-meta mt-5 rounded-[1.35rem] bg-[var(--warning-soft)] px-4 py-3 text-[var(--warning)]">
          Баланс близок к порогу запуска. Проверьте кредиты перед следующей генерацией.
        </p>
      ) : null}
    </article>
  );
}

function WorkspaceQuickActions() {
  const { bootstrap } = useWorkspaceRuntime();

  if (!bootstrap) {
    return null;
  }

  return (
    <section className="grid gap-5 xl:grid-cols-4">
      {bootstrap.quick_actions.map((action) => (
        <article className="site-card flex flex-col p-7 lg:p-8" key={action.id}>
          <h2 className="workspace-card-title">{action.label}</h2>
          <p className="workspace-body mt-4 flex-1">{action.description}</p>
          {action.capability ? (
            <WorkspaceCapabilityCta capability={action.capability} className="mt-8 w-full" href={action.href} variant="soft">
              Открыть
            </WorkspaceCapabilityCta>
          ) : <SiteButton className="mt-8 w-full" href={action.href} variant="soft">Открыть</SiteButton>}
        </article>
      ))}
    </section>
  );
}

function WorkspaceBusinessState() {
  const { bootstrap, hasCapability } = useWorkspaceRuntime();

  if (!bootstrap) {
    return null;
  }

  if (!bootstrap.business_profile.exists) {
    return (
      <div className="site-card p-8 lg:p-10">
        <p className="eyebrow">B2B-контур</p>
        <h2 className="workspace-section-title mt-4">Бизнес-профиль еще не подключен</h2>
        <p className="workspace-body mt-4 max-w-[860px]">
          Вы уже можете собирать карточки товара и готовить ручную выгрузку. Бизнес-профиль нужен для брендового контекста, каналов публикации и будущих интеграций магазина.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <WorkspaceCapabilityCta capability="business_profile_manage" href="/workspace/business-profile" variant="violet">
            Настроить бизнес-профиль
          </WorkspaceCapabilityCta>
          <WorkspaceCapabilityCta capability="product_card_create" href="/workspace/product-card" variant="secondary">
            Открыть карточку товара
          </WorkspaceCapabilityCta>
        </div>
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="rounded-[1.6rem] border border-[var(--border)] bg-[var(--surface)] p-5">
            <p className="workspace-meta">Ручная выгрузка</p>
            <p className="workspace-body mt-3">
              {hasCapability("manual_export")
                ? "Доступна уже сейчас без подключения магазина."
                : "Появится после активации этой возможности на сервере."}
            </p>
          </div>
          <div className="rounded-[1.6rem] border border-[var(--border)] bg-[var(--surface)] p-5">
            <p className="workspace-meta">Шаблоны бренда</p>
            <p className="workspace-body mt-3">Откроются после сохранения профиля бизнеса.</p>
          </div>
          <div className="rounded-[1.6rem] border border-[var(--border)] bg-[var(--surface)] p-5">
            <p className="workspace-meta">Публикация и синхронизация</p>
            <p className="workspace-body mt-3">Останутся закрыты, пока не подключена интеграция магазина.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="site-card p-8 lg:p-10">
      <p className="eyebrow">B2B-контур</p>
      <h2 className="workspace-section-title mt-4">Бизнес-профиль активен</h2>
      <p className="workspace-body mt-4">{bootstrap.business_profile.display_name ?? "Профиль бизнеса подключен."}</p>
    </div>
  );
}

function WorkspaceRecentJobs() {
  const { bootstrap } = useWorkspaceRuntime();

  if (!bootstrap) {
    return null;
  }

  if (bootstrap.recent_jobs.length === 0) {
    return (
      <div className="site-card p-8 lg:p-10">
        <h2 className="workspace-section-title">История еще не заполнена</h2>
        <p className="workspace-body mt-4 max-w-[780px]">
          После первых задач здесь появятся последние примерки, продуктовые сценарии и результаты. Пока интерфейс честно показывает пустое состояние без поддельной истории.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <WorkspaceCapabilityCta capability="try_on_create" href="/workspace/new-fitting" variant="violet">
            Запустить первую примерку
          </WorkspaceCapabilityCta>
          <WorkspaceCapabilityCta capability="product_card_create" href="/workspace/product-card" variant="secondary">
            Открыть B2B-сценарий
          </WorkspaceCapabilityCta>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-5 lg:grid-cols-3">
      {bootstrap.recent_jobs.map((job) => (
        <article className="site-card p-7 lg:p-8" key={job.job_id}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="workspace-meta uppercase tracking-[0.12em]">{job.workflow_type}</p>
              <h3 className="workspace-card-title mt-3">{job.title}</h3>
            </div>
            <span className="rounded-full bg-[var(--ai-soft)] px-3 py-2 text-[0.78rem] font-semibold text-[var(--ai)]">{job.status}</span>
          </div>
          {job.summary ? <p className="workspace-body mt-4">{job.summary}</p> : null}
          <p className="workspace-meta mt-5">{job.updated_at}</p>
          <SiteButton className="mt-7" href={job.href} variant="soft">
            Открыть
          </SiteButton>
        </article>
      ))}
    </div>
  );
}

export function WorkspaceDashboard() {
  const { bootstrap } = useWorkspaceRuntime();

  if (!bootstrap) {
    return null;
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <div className="flex flex-wrap items-start justify-between gap-8">
          <div className="max-w-[840px]">
            <p className="eyebrow">Единая рабочая зона</p>
            <h1 className="workspace-page-title mt-4">
              {bootstrap.user.first_name ? `${bootstrap.user.first_name}, продолжаем работу` : "Рабочая зона FitFabrica"}
            </h1>
            <p className="workspace-page-lead mt-4">
              Единый кабинет для примерки, поиска похожих товаров, карточек товара, кредитов и бизнес-настроек. Сервер управляет доступными сценариями и данными, а интерфейс показывает только актуальное состояние.
            </p>
          </div>
          <div className="max-w-[320px] rounded-[2rem] border border-[var(--border)] bg-[var(--surface-alt)] p-6">
            <p className="workspace-meta uppercase tracking-[0.14em]">Интеграции</p>
            <p className="workspace-card-title mt-4">
              {bootstrap.integrations.has_connected_store ? "Магазин подключен" : "Магазин еще не подключен"}
            </p>
            <p className="workspace-body mt-3">
              Ручная выгрузка и генерация доступны без магазина. Автопубликация откроется после подключения интеграции.
            </p>
          </div>
        </div>
      </section>

      <section className="mt-[50px]">
        <WorkspaceCreditsCard />
      </section>

      <section className="mt-[50px]">
        <WorkspaceQuickActions />
      </section>

      <section className="mt-[50px]">
        <WorkspaceBusinessState />
      </section>

      <section className="mt-[50px]">
        <WorkspaceRecentJobs />
      </section>
    </main>
  );
}
