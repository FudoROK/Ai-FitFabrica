"use client";

import { useState } from "react";
import type { NoBillingReadinessResponse, ReadinessService, ReadinessServiceStatus } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

type ReadinessState = "locked" | "empty" | "loading" | "ready" | "error";

const ADMIN_UI_ENABLED = process.env.NEXT_PUBLIC_ENABLE_ADMIN_READINESS_UI === "true";

const STATUS_LABELS: Record<ReadinessServiceStatus, string> = {
  blocked: "Blocked",
  configured: "Configured",
  disabled: "Disabled",
  ready: "Ready",
};

export function AdminReadinessDashboard() {
  const [statusToken, setStatusToken] = useState("");
  const [readiness, setReadiness] = useState<NoBillingReadinessResponse | null>(null);
  const [error, setError] = useState("");
  const [state, setState] = useState<ReadinessState>(ADMIN_UI_ENABLED ? "empty" : "locked");
  const isLoading = state === "loading";

  async function loadReadiness() {
    if (!ADMIN_UI_ENABLED) {
      setState("locked");
      return;
    }
    if (statusToken.trim().length === 0) {
      setReadiness(null);
      setState("empty");
      return;
    }
    setState("loading");
    setError("");
    try {
      const response = await apiClient().getNoBillingReadiness(statusToken.trim());
      setReadiness(response);
      setState("ready");
    } catch (requestError) {
      setReadiness(null);
      setError(requestError instanceof Error ? requestError.message : "Backend readiness request failed.");
      setState("error");
    }
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-8 lg:px-10 lg:py-12">
      <section className="mx-auto max-w-[1180px]">
        <p className="eyebrow">Admin Readiness</p>
        <h1 className="workspace-page-title mt-4">No-billing project readiness</h1>
        <p className="workspace-page-lead mt-4 max-w-[900px]">
          Backend-owned status for what can be tested now and what must wait for billing, auth, provider access, or approved discovery sources.
        </p>

        {state === "locked" ? (
          <StatusPanel
            message="Admin readiness UI is disabled. Enable NEXT_PUBLIC_ENABLE_ADMIN_READINESS_UI=true only for an internal environment."
            title="locked"
          />
        ) : (
          <div className="mt-8 grid gap-4 rounded-[28px] border border-[var(--border)] bg-white/80 p-5 lg:grid-cols-[1fr_auto]">
            <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
              Status endpoint token
              <input
                className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--text-primary)]"
                onChange={(event) => setStatusToken(event.target.value)}
                placeholder="Paste STATUS_ENDPOINT_TOKEN"
                type="password"
                value={statusToken}
              />
            </label>
            <button
              className="self-end rounded-full bg-[var(--text-primary)] px-6 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
              disabled={isLoading || statusToken.trim().length === 0}
              onClick={() => void loadReadiness()}
              type="button"
            >
              Load readiness
            </button>
          </div>
        )}
      </section>

      <section className="mx-auto mt-8 max-w-[1180px]">
        {state === "empty" ? <StatusPanel message="Enter a status endpoint token to load backend readiness." title="empty" /> : null}
        {state === "loading" ? <StatusPanel message="Loading backend readiness from /ready." title="loading" /> : null}
        {state === "error" ? <StatusPanel message={error} title="error" /> : null}
        {state === "ready" && readiness ? <ReadinessReport readiness={readiness} /> : null}
      </section>
    </main>
  );
}

function ReadinessReport({ readiness }: { readiness: NoBillingReadinessResponse }) {
  const serviceEntries = Object.entries(readiness.services);
  return (
    <div className="grid gap-6">
      <section className="grid gap-4 rounded-[28px] border border-[var(--border)] bg-white/85 p-6 md:grid-cols-3">
        <SummaryMetric label="Mode" value={readiness.mode} />
        <SummaryMetric label="Overall" value={readiness.ok ? "Ready" : "Blocked"} />
        <SummaryMetric label="Blockers" value={String(readiness.blockers.length)} />
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {serviceEntries.map(([name, service]) => (
          <ServiceCard key={name} name={name} service={service} />
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        <ListPanel items={readiness.blockers} title="blockers" />
        <ListPanel items={readiness.safe_without_billing} title="safe_without_billing" />
        <ListPanel items={readiness.post_billing_checks} title="post_billing_checks" />
      </section>
    </div>
  );
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="eyebrow">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-[var(--text-primary)]">{value}</p>
    </div>
  );
}

function ServiceCard({ name, service }: { name: string; service: ReadinessService }) {
  return (
    <article className="rounded-[24px] border border-[var(--border)] bg-white/85 p-5">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-base font-semibold text-[var(--text-primary)]">{formatToken(name)}</h2>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClassName(service.status)}`}>
          {STATUS_LABELS[service.status]}
        </span>
      </div>
      <p className="workspace-body mt-4">{service.detail}</p>
    </article>
  );
}

function ListPanel({ items, title }: { items: string[]; title: string }) {
  return (
    <article className="rounded-[28px] border border-[var(--border)] bg-white/85 p-5">
      <h2 className="text-base font-semibold text-[var(--text-primary)]">{title}</h2>
      {items.length > 0 ? (
        <ul className="mt-4 grid gap-2 text-sm text-[var(--text-muted)]">
          {items.map((item) => (
            <li className="rounded-2xl bg-[var(--surface-muted)] px-3 py-2" key={item}>
              {formatToken(item)}
            </li>
          ))}
        </ul>
      ) : (
        <p className="workspace-body mt-4">No items.</p>
      )}
    </article>
  );
}

function StatusPanel({ message, title }: { message: string; title: string }) {
  return (
    <div className="rounded-[28px] border border-[var(--border)] bg-white/85 p-6">
      <p className="eyebrow">{title}</p>
      <p className="workspace-body mt-3">{message}</p>
    </div>
  );
}

function statusClassName(status: ReadinessServiceStatus): string {
  if (status === "blocked") {
    return "bg-rose-50 text-rose-700";
  }
  if (status === "configured" || status === "ready") {
    return "bg-emerald-50 text-emerald-700";
  }
  return "bg-slate-100 text-slate-700";
}

function formatToken(value: string): string {
  return value.replaceAll("_", " ");
}

function apiClient(): WebApiClient {
  return new WebApiClient(getApiBaseUrl());
}
