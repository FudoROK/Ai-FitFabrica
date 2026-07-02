"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

const CHANNEL_OPTIONS = [
  { value: "instagram", label: "Instagram" },
  { value: "wildberries", label: "Wildberries" },
  { value: "ozon", label: "Ozon" },
  { value: "shopify", label: "Shopify" },
] as const;

export function WorkspaceBusinessProfileForm() {
  const { bootstrap, refresh } = useWorkspaceRuntime();
  const [displayName, setDisplayName] = useState("");
  const [channels, setChannels] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let isActive = true;

    async function loadProfile() {
      if (!bootstrap) {
        return;
      }

      setDisplayName(bootstrap.business_profile.display_name ?? "");
      setChannels(bootstrap.business_profile.channels);

      try {
        const client = new WebApiClient(getApiBaseUrl());
        const profile = await client.getWorkspaceBusinessProfile();
        if (!isActive) {
          return;
        }
        setDisplayName(profile.display_name);
        setChannels(profile.channels);
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

    void loadProfile();

    return () => {
      isActive = false;
    };
  }, [bootstrap]);

  function toggleChannel(channel: string, checked: boolean) {
    setChannels((current) => {
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

    if (!displayName.trim()) {
      setError("Укажите название бренда или бизнеса.");
      return;
    }

    setIsSubmitting(true);

    try {
      const client = new WebApiClient(getApiBaseUrl());
      await client.saveWorkspaceBusinessProfile({
        display_name: displayName.trim(),
        channels,
      });
      await refresh();
      setSuccess("Бизнес-профиль сохранен.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось сохранить бизнес-профиль.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Бизнес-профиль</p>
        <h1 className="workspace-page-title mt-4">Профиль бизнеса</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Бизнес-профиль хранит брендовый контекст, каналы и правила публикации на backend. Он отделен от product workflow и не притворяется частью генерации.
        </p>
      </section>

      <form className="mt-[50px] grid gap-5 xl:grid-cols-[1.1fr_0.9fr]" onSubmit={handleSubmit}>
        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Данные профиля</h2>
          <div className="mt-6 grid gap-6">
            <label className="public-form-label grid gap-3">
              <span>Название бренда или бизнеса</span>
              <input
                className="site-input"
                disabled={isLoading || isSubmitting}
                onChange={(event) => setDisplayName(event.target.value)}
                value={displayName}
              />
            </label>

            <fieldset className="grid gap-3">
              <legend className="public-form-label">Каналы публикации</legend>
              <div className="grid gap-3">
                {CHANNEL_OPTIONS.map((option) => (
                  <label className="public-body flex items-center gap-4" key={option.value}>
                    <input
                      checked={channels.includes(option.value)}
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
              {isSubmitting ? "Сохраняем профиль" : "Сохранить профиль"}
            </SiteButton>
            <SiteButton href="/workspace/settings" variant="secondary">
              Вернуться в настройки
            </SiteButton>
          </div>
        </section>

        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Что это меняет</h2>
          <div className="mt-6 grid gap-4">
            <div className="rounded-[1.5rem] border border-[var(--border)] p-5">
              <p className="workspace-card-title">Контекст бренда</p>
              <p className="workspace-body mt-3">Backend получает единое имя бизнеса и может использовать его в product и content workflows.</p>
            </div>
            <div className="rounded-[1.5rem] border border-[var(--border)] p-5">
              <p className="workspace-card-title">Каналы</p>
              <p className="workspace-body mt-3">Выбранные каналы становятся persisted state и доступны для интеграций и будущей публикации.</p>
            </div>
            <div className="rounded-[1.5rem] border border-[var(--border)] p-5">
              <p className="workspace-card-title">Следующий шаг</p>
              <p className="workspace-body mt-3">После сохранения можно переходить к интеграциям и подключать магазин уже на основе сохраненного профиля.</p>
            </div>
          </div>
        </section>
      </form>
    </main>
  );
}
