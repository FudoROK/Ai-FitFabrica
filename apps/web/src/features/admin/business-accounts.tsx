"use client";

import { useState } from "react";
import type {
  AdminBusinessCatalogCredentials,
  AdminBusinessCatalogMerchantTierCard,
  BusinessCatalogTenantTier,
} from "@/lib/api/business-catalog-contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

type ReviewState = "loading" | "ready" | "empty" | "error" | "locked";

const ADMIN_UI_ENABLED = process.env.NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI === "true";

export function AdminBusinessAccounts() {
  const [adminToken, setAdminToken] = useState("");
  const [accounts, setAccounts] = useState<AdminBusinessCatalogMerchantTierCard[]>([]);
  const [error, setError] = useState("");
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [state, setState] = useState<ReviewState>(ADMIN_UI_ENABLED ? "empty" : "locked");
  const [submittingMerchantId, setSubmittingMerchantId] = useState<string | null>(null);

  const canLoad = ADMIN_UI_ENABLED && adminToken.trim().length > 0;
  const credentials: AdminBusinessCatalogCredentials = {
    adminToken: adminToken.trim(),
  };

  async function loadAccounts() {
    if (!canLoad) {
      setAccounts([]);
      setState(ADMIN_UI_ENABLED ? "empty" : "locked");
      return;
    }
    setState("loading");
    setError("");
    try {
      const response = await apiClient().getAdminBusinessCatalogMerchantTiers(credentials);
      setAccounts(response.merchants);
      setState(response.merchants.length > 0 ? "ready" : "empty");
    } catch (requestError) {
      setAccounts([]);
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить B2B клиентов.");
      setState("error");
    }
  }

  async function assignTier(merchantId: string, assignedTier: BusinessCatalogTenantTier) {
    const reason = reasons[merchantId]?.trim() ?? "";
    if (!reason) {
      setError("Укажите причину решения перед назначением tier.");
      setState("error");
      return;
    }
    setSubmittingMerchantId(merchantId);
    setError("");
    try {
      await apiClient().assignAdminBusinessCatalogMerchantTier(
        merchantId,
        { assigned_tier: assignedTier, reason },
        credentials,
      );
      await loadAccounts();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось назначить tier клиента.");
      setState("error");
    } finally {
      setSubmittingMerchantId(null);
    }
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-8 lg:px-10 lg:py-12">
      <section className="site-card mx-auto max-w-[1180px] p-8 lg:p-10">
        <p className="eyebrow">Admin Business Accounts</p>
        <h1 className="workspace-page-title mt-4">B2B клиенты и нагрузочные tier</h1>
        <p className="workspace-page-lead mt-4 max-w-[900px]">
          Система показывает рекомендацию по нагрузке, но не переводит клиента автоматически.
          Назначенный tier меняет только администратор с явной причиной решения.
        </p>

        {state === "locked" ? (
          <StatusPanel
            title="Админ-панель выключена"
            message="Включите NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI=true только для внутреннего окружения."
          />
        ) : (
          <div className="mt-8 grid gap-4 rounded-[28px] border border-[var(--border)] bg-white/80 p-5 lg:grid-cols-[1fr_auto]">
            <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
              Admin access token
              <input
                className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--text-primary)]"
                onChange={(event) => setAdminToken(event.target.value)}
                placeholder="Paste admin access token"
                type="password"
                value={adminToken}
              />
            </label>
            <button
              className="self-end rounded-full bg-[var(--text-primary)] px-6 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
              disabled={!canLoad || state === "loading"}
              onClick={() => void loadAccounts()}
              type="button"
            >
              Загрузить клиентов
            </button>
          </div>
        )}
      </section>

      <section className="mx-auto mt-8 max-w-[1180px]">
        {state === "loading" ? <StatusPanel title="loading" message="Загружаю B2B клиентов из backend." /> : null}
        {state === "empty" ? <StatusPanel title="empty" message="Нет B2B клиентов или не указан admin actor id." /> : null}
        {state === "error" ? <StatusPanel title="error" message={error} /> : null}
        {state === "ready" ? (
          <div className="grid gap-5">
            {accounts.map((account) => {
              const isSubmitting = submittingMerchantId === account.merchant.merchant_id;
              return (
                <article className="site-card p-6" key={account.merchant.merchant_id}>
                  <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
                    <div>
                      <p className="eyebrow">{account.hot_account_mode ? "dedicated" : "shared"}</p>
                      <h2 className="workspace-card-title mt-3">{account.merchant.display_name}</h2>
                      <p className="workspace-body mt-3">
                        Назначенный tier: <strong>{account.assigned_tier}</strong> · Рекомендация системы:{" "}
                        <strong>{account.recommended_tier}</strong>
                      </p>
                      <p className="workspace-body mt-2">
                        Причины:{" "}
                        {account.recommendation_reasons.length > 0
                          ? account.recommendation_reasons.join(", ")
                          : "нет"}
                      </p>
                    </div>
                    <div className="rounded-[22px] border border-[var(--border)] bg-white/70 p-4 text-sm">
                      <p>Products: {account.metrics.product_count}</p>
                      <p>Imports 30d: {account.metrics.imports_last_30_days}</p>
                      <p>Largest CSV: {account.metrics.largest_import_rows}</p>
                      <p>Images 30d: {account.metrics.images_last_30_days}</p>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 text-sm text-[var(--text-muted)]">
                    <p>Queue: {account.queue_partition}</p>
                    <p>Rate limit: {account.rate_limit_bucket}</p>
                    <p>Storage: {account.storage_prefix}</p>
                  </div>

                  <div className="mt-6 rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
                    <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                      Причина решения
                      <input
                        className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                        onChange={(event) =>
                          setReasons((current) => ({
                            ...current,
                            [account.merchant.merchant_id]: event.target.value,
                          }))
                        }
                        placeholder="Например: крупный импорт товаров или снижение нагрузки"
                        value={reasons[account.merchant.merchant_id] ?? ""}
                      />
                    </label>
                    <div className="mt-4 flex flex-wrap gap-3">
                      <button
                        className="rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={isSubmitting}
                        onClick={() => void assignTier(account.merchant.merchant_id, "standard")}
                        type="button"
                      >
                        Вернуть в standard
                      </button>
                      <button
                        className="rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={isSubmitting}
                        onClick={() => void assignTier(account.merchant.merchant_id, "large")}
                        type="button"
                      >
                        Перевести в large
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        ) : null}
      </section>
    </main>
  );
}

function StatusPanel({ message, title }: { message: string; title: string }) {
  return (
    <div className="site-card p-8">
      <p className="eyebrow">{title}</p>
      <p className="workspace-body mt-4">{message}</p>
    </div>
  );
}

function apiClient(): WebApiClient {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("Admin API base URL is not configured.");
  }
  return new WebApiClient(baseUrl);
}
