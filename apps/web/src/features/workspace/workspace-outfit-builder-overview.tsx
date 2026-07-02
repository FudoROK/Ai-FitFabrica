"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { WorkspaceActionCard, WorkspaceSectionCard } from "@/features/workspace/workspace-section-primitives";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import { WorkspaceShellState } from "@/features/workspace/workspace-shell-state";
import type {
  WorkspaceOutfitBuilderBriefResponse,
  WorkspaceOutfitBuilderRequestResponse,
  WorkspaceOutfitBuilderRequestStatusResponse,
} from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

export function WorkspaceOutfitBuilderOverview() {
  const { bootstrap, error: runtimeError, isLoading: runtimeLoading, refresh } = useWorkspaceRuntime();
  const [brief, setBrief] = useState<WorkspaceOutfitBuilderBriefResponse | null>(null);
  const [recentRequests, setRecentRequests] = useState<WorkspaceOutfitBuilderRequestResponse[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<WorkspaceOutfitBuilderRequestStatusResponse | null>(null);
  const [submitResponse, setSubmitResponse] = useState<WorkspaceOutfitBuilderRequestResponse | null>(null);
  const [occasion, setOccasion] = useState("office");
  const [budget, setBudget] = useState("");
  const [baseItem, setBaseItem] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let isActive = true;

    async function loadScreen() {
      if (!bootstrap) {
        return;
      }

      try {
        const client = new WebApiClient(getApiBaseUrl());
        const [nextBrief, nextRequests] = await Promise.all([
          client.getWorkspaceOutfitBuilderBrief(),
          client.getWorkspaceOutfitBuilderRequests(),
        ]);

        if (!isActive) {
          return;
        }

        setBrief(nextBrief);
        setRecentRequests(nextRequests.requests);
        setError("");

        if (nextRequests.requests[0]) {
          const status = await client.getWorkspaceOutfitBuilderRequestStatus(nextRequests.requests[0].request_id);
          if (isActive) {
            setSelectedStatus(status);
          }
        } else if (isActive) {
          setSelectedStatus(null);
        }
      } catch (requestError) {
        if (!isActive) {
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить данные outfit-builder.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadScreen();

    return () => {
      isActive = false;
    };
  }, [bootstrap]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitResponse(null);

    if (!occasion.trim()) {
      setError("Укажите повод или сценарий для образа.");
      return;
    }

    setIsSubmitting(true);

    try {
      const client = new WebApiClient(getApiBaseUrl());
      const response = await client.createWorkspaceOutfitBuilderRequest({
        occasion: occasion.trim(),
        budget: budget.trim() || null,
        base_item: baseItem.trim() || null,
      });
      const status = await client.getWorkspaceOutfitBuilderRequestStatus(response.request_id);
      setSubmitResponse(response);
      setSelectedStatus(status);
      setRecentRequests((current) => {
        const completedRow: WorkspaceOutfitBuilderRequestResponse = {
          ...response,
          status: "accepted",
          message: status.status_history.at(-1)?.message ?? response.message,
        };
        return [completedRow, ...current.filter((item) => item.request_id !== response.request_id)];
      });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось создать запрос outfit-builder.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const combinedError = runtimeError || error;
  const combinedLoading = runtimeLoading || isLoading;

  if (combinedLoading || combinedError || !bootstrap || !brief) {
    return (
      <WorkspaceShellState
        error={combinedError}
        hasBootstrap={Boolean(bootstrap && brief)}
        isLoading={combinedLoading}
        onRetry={refresh}
      />
    );
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">{brief.hero_title}</p>
        <h1 className="workspace-page-title mt-4">{brief.hero_title}</h1>
        <p className="workspace-page-lead mt-4 max-w-[860px]">{brief.hero_description}</p>
      </section>

      <section className="mt-[50px] grid gap-5 xl:grid-cols-[1fr_0.95fr]">
        <div className="grid gap-5">
          <WorkspaceSectionCard title="Входные данные">
            <ul className="mt-4 grid gap-3">
              {brief.input_sections.map((item) => (
                <li className="workspace-body" key={item}>
                  {item}
                </li>
              ))}
            </ul>
          </WorkspaceSectionCard>

          <WorkspaceSectionCard title="Результат">
            <ul className="mt-4 grid gap-3">
              {brief.result_sections.map((item) => (
                <li className="workspace-body" key={item}>
                  {item}
                </li>
              ))}
            </ul>
          </WorkspaceSectionCard>

          <WorkspaceSectionCard title="Недавние заявки">
            {recentRequests.length > 0 ? (
              <ul className="mt-4 grid gap-3">
                {recentRequests.map((request) => (
                  <li className="rounded-3xl border border-black/8 bg-white/80 px-5 py-4" key={request.request_id}>
                    <p className="workspace-body font-semibold">{request.occasion}</p>
                    <p className="workspace-body mt-1 text-[var(--foreground-muted)]">
                      {request.base_item ?? "Базовая вещь будет уточнена"} · {request.budget ?? "Бюджет не указан"}
                    </p>
                    <p className="workspace-caption mt-2">{request.message}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="workspace-body mt-4">Пока нет заявок. Создайте первую, и она появится здесь.</p>
            )}
          </WorkspaceSectionCard>

          <WorkspaceSectionCard title="Статус заявки">
            {selectedStatus ? (
              <div className="mt-4 grid gap-4">
                <p className="workspace-body font-semibold">{selectedStatus.result_summary.headline}</p>
                <ul className="grid gap-2">
                  {selectedStatus.result_summary.summary_lines.map((line) => (
                    <li className="workspace-body" key={line}>
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="workspace-body mt-4">После создания заявки здесь появится backend-owned статус.</p>
            )}
          </WorkspaceSectionCard>

          <WorkspaceSectionCard title="Готовность">
            <p className="workspace-body mt-4">{brief.readiness_note}</p>
          </WorkspaceSectionCard>
        </div>

        <form className="grid gap-5" onSubmit={handleSubmit}>
          <WorkspaceSectionCard title="Создать запрос">
            <div className="mt-4 grid gap-5">
              <label className="public-form-label grid gap-3">
                <span>Повод или сценарий</span>
                <input
                  className="site-input"
                  disabled={isSubmitting}
                  onChange={(event) => setOccasion(event.target.value)}
                  value={occasion}
                />
              </label>
              <label className="public-form-label grid gap-3">
                <span>Бюджет</span>
                <input
                  className="site-input"
                  disabled={isSubmitting}
                  onChange={(event) => setBudget(event.target.value)}
                  placeholder="Например, 150"
                  value={budget}
                />
              </label>
              <label className="public-form-label grid gap-3">
                <span>Базовая вещь</span>
                <input
                  className="site-input"
                  disabled={isSubmitting}
                  onChange={(event) => setBaseItem(event.target.value)}
                  placeholder="Например, black blazer"
                  value={baseItem}
                />
              </label>
            </div>
            {submitResponse ? (
              <p className="mt-6 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">
                {submitResponse.message}
              </p>
            ) : null}
          </WorkspaceSectionCard>

          <WorkspaceActionCard>
            <div className="flex flex-wrap gap-3">
              <SiteButton disabled={isSubmitting} type="submit" variant="violet">
                {isSubmitting ? "Создаем запрос" : "Создать запрос"}
              </SiteButton>
              <SiteButton href="/workspace/new-fitting" variant="secondary">
                Вернуться к примерке
              </SiteButton>
              <SiteButton href="/workspace/similar-search" variant="secondary">
                Открыть похожие товары
              </SiteButton>
            </div>
          </WorkspaceActionCard>
        </form>
      </section>
    </main>
  );
}
