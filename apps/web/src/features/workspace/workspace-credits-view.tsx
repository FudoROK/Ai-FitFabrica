"use client";

import { useEffect, useState } from "react";
import { WorkspaceCapabilityCta } from "@/features/workspace/workspace-capability-cta";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import type { CreditBalanceResponse, CreditLedgerResponse } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

export function WorkspaceCreditsView() {
  const { bootstrap } = useWorkspaceRuntime();
  const [balance, setBalance] = useState<CreditBalanceResponse | null>(null);
  const [ledger, setLedger] = useState<CreditLedgerResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadCredits() {
      if (!bootstrap) {
        return;
      }

      try {
        const client = new WebApiClient(getApiBaseUrl());
        const [nextBalance, nextLedger] = await Promise.all([
          client.getCreditBalance(bootstrap.credit_owner.owner_type, bootstrap.credit_owner.owner_id),
          client.getCreditLedger(bootstrap.credit_owner.owner_type, bootstrap.credit_owner.owner_id, 10),
        ]);
        setBalance(nextBalance);
        setLedger(nextLedger);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить кредиты.");
      }
    }

    void loadCredits();
  }, [bootstrap]);

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Кредиты</p>
        <h1 className="workspace-page-title mt-4">Баланс и история списаний</h1>
        <p className="workspace-page-lead mt-4 max-w-[860px]">
          На аккаунт действует единый баланс. Профиль бизнеса не создает отдельный кошелек: кредиты, возвраты и будущие пополнения сходятся в одном владельце.
        </p>
      </section>

      <section className="mt-[50px] grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <article className="site-card p-7 lg:p-8">
          <p className="eyebrow">Доступно</p>
          <strong className="workspace-kpi mt-4 block">{balance?.available_credits ?? bootstrap?.credits.balance ?? 0}</strong>
          <p className="workspace-body mt-4">
            Зарезервировано: {balance?.reserved_credits ?? 0}. Данные пришли из backend API, без локальных фиктивных чисел.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <WorkspaceCapabilityCta capability="try_on_create" href="/workspace/new-fitting" variant="violet">
              Запустить примерку
            </WorkspaceCapabilityCta>
            <WorkspaceCapabilityCta capability="product_card_create" href="/workspace/product-card" variant="secondary">
              Открыть B2B-сценарий
            </WorkspaceCapabilityCta>
          </div>
        </article>

        <article className="site-card p-7 lg:p-8">
          <p className="eyebrow">Состояние возможностей</p>
          <div className="mt-5 grid gap-4">
            <div className="rounded-[1.45rem] border border-[var(--border)] p-5">
              <p className="workspace-meta">Ручная выгрузка</p>
              <p className="workspace-body mt-2">Доступна без подключения магазина, если эта возможность включена на сервере.</p>
            </div>
            <div className="rounded-[1.45rem] border border-[var(--border)] p-5">
              <p className="workspace-meta">Публикация и синхронизация</p>
              <p className="workspace-body mt-2">Останутся закрытыми, пока раздел интеграций не покажет подключенный магазин.</p>
            </div>
          </div>
        </article>
      </section>

      <section className="mt-[50px] site-card p-7 lg:p-8">
        <p className="eyebrow">История баланса</p>
        <h2 className="workspace-section-title mt-4">Последние операции</h2>
        {error ? (
          <p className="workspace-meta mt-6 rounded-[1.35rem] bg-[var(--warning-soft)] px-4 py-3 text-[var(--warning)]">{error}</p>
        ) : null}
        {ledger && ledger.events.length > 0 ? (
          <div className="mt-8 grid gap-4">
            {ledger.events.map((event) => (
              <div className="rounded-[1.45rem] border border-[var(--border)] bg-[var(--surface)] p-5" key={event.event_id}>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="workspace-meta uppercase tracking-[0.12em]">{event.event_type}</p>
                    <p className="workspace-body mt-2">
                      {event.workflow_type ?? "manual"}
                      {event.stage_name ? ` • ${event.stage_name}` : ""}
                    </p>
                    <p className="workspace-meta mt-2">{event.created_at ?? "Временная метка появится с первым событием."}</p>
                  </div>
                  <strong className={`ui-label-strong ${event.credits_delta > 0 ? "text-[var(--success)]" : "text-[var(--error)]"}`}>
                    {event.credits_delta > 0 ? "+" : ""}
                    {event.credits_delta}
                  </strong>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-8 rounded-[1.6rem] border border-dashed border-[var(--border)] p-8">
            <h3 className="workspace-card-title">История пока пуста</h3>
            <p className="workspace-body mt-3 max-w-[760px]">
              После первых операций сервер начнет возвращать реальные события по балансу. Пока интерфейс честно показывает пустое состояние вместо выдуманных транзакций.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
