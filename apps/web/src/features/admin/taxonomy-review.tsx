"use client";

import { useState } from "react";
import type { AdminTaxonomyCandidate, AdminTaxonomyCredentials } from "@/lib/api/admin-contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

type ReviewState = "loading" | "ready" | "empty" | "error" | "locked";

const ADMIN_UI_ENABLED = process.env.NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI === "true";

export function AdminTaxonomyReview() {
  const [adminToken, setAdminToken] = useState("");
  const [candidates, setCandidates] = useState<AdminTaxonomyCandidate[]>([]);
  const [error, setError] = useState("");
  const [mergeTargets, setMergeTargets] = useState<Record<string, string>>({});
  const [renameCodes, setRenameCodes] = useState<Record<string, string>>({});
  const [renameDisplayNames, setRenameDisplayNames] = useState<Record<string, string>>({});
  const [rejectReasons, setRejectReasons] = useState<Record<string, string>>({});
  const [state, setState] = useState<ReviewState>(ADMIN_UI_ENABLED ? "loading" : "locked");
  const [submittingCandidateId, setSubmittingCandidateId] = useState<string | null>(null);

  const canLoad = ADMIN_UI_ENABLED && adminToken.trim().length > 0;
  const credentials: AdminTaxonomyCredentials = {
    adminToken: adminToken.trim(),
  };

  async function loadCandidates() {
    if (!canLoad) {
      setState(ADMIN_UI_ENABLED ? "empty" : "locked");
      return;
    }
    setState("loading");
    setError("");
    try {
      const response = await apiClient().getAdminTaxonomyCandidates(credentials);
      setCandidates(response.candidates);
      setState(response.candidates.length > 0 ? "ready" : "empty");
    } catch (requestError) {
      setCandidates([]);
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить кандидатов.");
      setState("error");
    }
  }

  async function approve(candidateId: string) {
    await mutate(candidateId, () => apiClient().approveAdminTaxonomyCandidate(candidateId, credentials));
  }

  async function reject(candidateId: string) {
    const reason = rejectReasons[candidateId]?.trim() ?? "";
    if (!reason) {
      setError("Укажите причину отклонения.");
      setState("error");
      return;
    }
    await mutate(candidateId, () =>
      apiClient().rejectAdminTaxonomyCandidate(candidateId, { review_reason: reason }, credentials),
    );
  }

  async function merge(candidateId: string) {
    const target = mergeTargets[candidateId]?.trim() ?? "";
    if (!target) {
      setError("Укажите существующий код каталога для объединения.");
      setState("error");
      return;
    }
    await mutate(candidateId, () =>
      apiClient().mergeAdminTaxonomyCandidate(candidateId, { target_catalog_item_code: target }, credentials),
    );
  }

  async function renameAndApprove(candidateId: string) {
    const approvedCode = renameCodes[candidateId]?.trim() ?? "";
    const approvedDisplayName = renameDisplayNames[candidateId]?.trim() ?? "";
    if (!approvedCode || !approvedDisplayName) {
      setError("Укажите новый код и название для rename-and-approve.");
      setState("error");
      return;
    }
    await mutate(candidateId, () =>
      apiClient().renameAndApproveAdminTaxonomyCandidate(
        candidateId,
        {
          approved_catalog_item_code: approvedCode,
          approved_display_name: approvedDisplayName,
        },
        credentials,
      ),
    );
  }

  async function mutate(
    candidateId: string,
    operation: () => Promise<{ candidate: AdminTaxonomyCandidate }>,
  ) {
    setSubmittingCandidateId(candidateId);
    setError("");
    try {
      await operation();
      await loadCandidates();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось выполнить действие.");
      setState("error");
    } finally {
      setSubmittingCandidateId(null);
    }
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-8 lg:px-10 lg:py-12">
      <section className="site-card mx-auto max-w-[1180px] p-8 lg:p-10">
        <p className="eyebrow">Admin Taxonomy</p>
        <h1 className="workspace-page-title mt-4">Проверка новых типов одежды</h1>
        <p className="workspace-page-lead mt-4 max-w-[900px]">
          Здесь администратор вручную проверяет предложения агента. Модель не меняет production-каталог сама:
          approve, reject и merge проходят только через backend, feature flag и audit log.
        </p>

        {state === "locked" ? (
          <StatusPanel
            title="Админ-панель выключена"
            message="Frontend UI заблокирован. Включите NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI=true только для внутреннего окружения."
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
              onClick={() => void loadCandidates()}
              type="button"
            >
              Загрузить кандидатов
            </button>
          </div>
        )}
      </section>

      <section className="mx-auto mt-8 max-w-[1180px]">
        {state === "loading" ? <StatusPanel title="loading" message="Загружаю кандидатов из backend." /> : null}
        {state === "empty" ? (
          <StatusPanel title="empty" message="Нет кандидатов для проверки или не указан admin actor id." />
        ) : null}
        {state === "error" ? <StatusPanel title="error" message={error} /> : null}
        {state === "ready" ? (
          <div className="grid gap-5">
            {candidates.map((candidate) => {
              const isSubmitting = submittingCandidateId === candidate.id;
              return (
                <article className="site-card p-6" key={candidate.id}>
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <p className="eyebrow">{candidate.status}</p>
                      <h2 className="workspace-card-title mt-3">{candidate.proposed_display_name}</h2>
                      <p className="workspace-body mt-3">
                        Код: <strong>{candidate.proposed_code}</strong> · Категория:{" "}
                        <strong>{candidate.proposed_category}</strong> · Confidence:{" "}
                        {Math.round(candidate.confidence * 100)}%
                      </p>
                    </div>
                    <button
                      className="rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={isSubmitting}
                      onClick={() => void approve(candidate.id)}
                      type="button"
                    >
                      Approve
                    </button>
                  </div>

                  <p className="workspace-body mt-5">{candidate.agent_reasoning_summary}</p>
                  <p className="workspace-body mt-3">
                    Предложенные controls:{" "}
                    {candidate.proposed_controls.length > 0 ? candidate.proposed_controls.join(", ") : "нет"}
                  </p>

                  <div className="mt-6 grid gap-4 lg:grid-cols-3">
                    <div className="rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
                      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                        Причина отклонения
                        <input
                          className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                          onChange={(event) =>
                            setRejectReasons((current) => ({ ...current, [candidate.id]: event.target.value }))
                          }
                          placeholder="Например: слишком широкая категория"
                          value={rejectReasons[candidate.id] ?? ""}
                        />
                      </label>
                      <button
                        className="mt-4 rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={isSubmitting}
                        onClick={() => void reject(candidate.id)}
                        type="button"
                      >
                        Reject
                      </button>
                    </div>

                    <div className="rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
                      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                        Merge target code
                        <input
                          className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                          onChange={(event) =>
                            setMergeTargets((current) => ({ ...current, [candidate.id]: event.target.value }))
                          }
                          placeholder="shirt"
                          value={mergeTargets[candidate.id] ?? ""}
                        />
                      </label>
                      <button
                        className="mt-4 rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={isSubmitting}
                        onClick={() => void merge(candidate.id)}
                        type="button"
                      >
                        Merge
                      </button>
                    </div>

                    <div className="rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
                      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                        Rename code
                        <input
                          className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                          onChange={(event) =>
                            setRenameCodes((current) => ({ ...current, [candidate.id]: event.target.value }))
                          }
                          placeholder="kimono_outer_layer"
                          value={renameCodes[candidate.id] ?? ""}
                        />
                      </label>
                      <label className="mt-3 grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                        Rename display name
                        <input
                          className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                          onChange={(event) =>
                            setRenameDisplayNames((current) => ({
                              ...current,
                              [candidate.id]: event.target.value,
                            }))
                          }
                          placeholder="Kimono Outer Layer"
                          value={renameDisplayNames[candidate.id] ?? ""}
                        />
                      </label>
                      <button
                        className="mt-4 rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={isSubmitting}
                        onClick={() => void renameAndApprove(candidate.id)}
                        type="button"
                      >
                        Rename and approve
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
