"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { useWorkspaceCapabilityVerdict } from "@/features/workspace/use-workspace-capability-verdict";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

const CHANNEL_OPTIONS = [
  { value: "instagram", label: "Instagram" },
  { value: "wildberries", label: "Wildberries" },
  { value: "ozon", label: "Ozon" },
  { value: "shopify", label: "Shopify" }
] as const;

export function WorkspaceIntegrationsForm() {
  const { bootstrap, refresh } = useWorkspaceRuntime();
  const [connectedChannels, setConnectedChannels] = useState<string[]>([]);
  const [hasConnectedStore, setHasConnectedStore] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { matrix } = useWorkspaceCapabilityVerdict({ enabled: Boolean(bootstrap) });

  useEffect(() => {
    let isActive = true;

    async function loadIntegrations() {
      if (!bootstrap) {
        return;
      }

      setConnectedChannels(bootstrap.integrations.connected_channels);
      setHasConnectedStore(bootstrap.integrations.has_connected_store);

      try {
        const client = new WebApiClient(getApiBaseUrl());
        const integrations = await client.getWorkspaceIntegrations();
        if (!isActive) {
          return;
        }
        setConnectedChannels(integrations.connected_channels);
        setHasConnectedStore(integrations.has_connected_store);
      } catch {
        if (!isActive) {
          return;
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadIntegrations();

    return () => {
      isActive = false;
    };
  }, [bootstrap]);

  function toggleChannel(channel: string, checked: boolean) {
    setConnectedChannels((current) => {
      if (checked) {
        return current.includes(channel) ? current : [...current, channel];
      }

      return current.filter((item) => item !== channel);
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);

    try {
      const client = new WebApiClient(getApiBaseUrl());
      await client.saveWorkspaceIntegrations({
        connected_channels: connectedChannels,
        has_connected_store: hasConnectedStore
      });
      await refresh();
      setSuccess("Интеграции сохранены.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось сохранить интеграции.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const publishGate = matrix?.capability_states.find((item) => item.capability === "marketplace_publish") ?? null;

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Интеграции</p>
        <h1 className="workspace-page-title mt-4">Подключение магазина и каналов</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Здесь хранится backend-owned состояние подключенных каналов и готовности магазина к публикации. Экран больше не декоративный: изменения сохраняются, попадают в workspace bootstrap и сразу проверяются capability matrix сервера.
        </p>
      </section>

      <form className="mt-[50px] grid gap-5 xl:grid-cols-[1.1fr_0.9fr]" onSubmit={handleSubmit}>
        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Текущее состояние</h2>
          <div className="mt-6 grid gap-6">
            <label className="public-form-label flex items-start gap-4">
              <input
                checked={hasConnectedStore}
                className="mt-1 h-5 w-5 accent-[var(--ai)]"
                disabled={isLoading || isSubmitting}
                onChange={(event) => setHasConnectedStore(event.target.checked)}
                type="checkbox"
              />
              <span>
                Магазин подключен
                <span className="public-body mt-2 block">
                  Включайте этот статус только когда backend действительно готов работать с публикацией и синхронизацией.
                </span>
              </span>
            </label>

            <fieldset className="grid gap-3">
              <legend className="public-form-label">Подключенные каналы</legend>
              <div className="grid gap-3">
                {CHANNEL_OPTIONS.map((option) => (
                  <label className="public-body flex items-center gap-4" key={option.value}>
                    <input
                      checked={connectedChannels.includes(option.value)}
                      className="h-5 w-5 accent-[var(--ai)]"
                      disabled={isLoading || isSubmitting}
                      onChange={(event) => toggleChannel(option.value, event.target.checked)}
                      type="checkbox"
                    />
                    <span>{option.label}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          </div>

          {error ? <p className="mt-6 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
          {success ? <p className="mt-6 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">{success}</p> : null}

          <div className="mt-8 flex flex-wrap gap-3">
            <SiteButton disabled={isLoading || isSubmitting} type="submit" variant="violet">
              {isSubmitting ? "Сохраняем интеграции" : "Сохранить интеграции"}
            </SiteButton>
            <SiteButton href="/workspace/settings" variant="secondary">
              Вернуться в настройки
            </SiteButton>
          </div>
        </section>

        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Что это дает</h2>
          <div className="mt-6 grid gap-4">
            <div className="rounded-[1.5rem] border border-[var(--border)] p-5">
              <p className="workspace-card-title">Единое состояние</p>
              <p className="workspace-body mt-3">
                Sidebar, dashboard и следующие workflow читают одно persisted состояние без frontend hardcode.
              </p>
            </div>
            <div className="rounded-[1.5rem] border border-[var(--border)] p-5">
              <p className="workspace-card-title">Контроль публикации</p>
              <p className="workspace-body mt-3">
                Флаг подключения магазина можно использовать как backend gate для publish, import и catalog sync.
              </p>
            </div>
            <div className="rounded-[1.5rem] border border-[var(--border)] p-5">
              <p className="workspace-card-title">Server verdict</p>
              <p className="workspace-body mt-3">
                {publishGate
                  ? `Publish capability: ${publishGate.enabled ? "доступна" : publishGate.disabled_reason ?? "закрыта"}.`
                  : "Capability matrix еще не загружена."}
              </p>
            </div>
          </div>
        </section>
      </form>
    </main>
  );
}
