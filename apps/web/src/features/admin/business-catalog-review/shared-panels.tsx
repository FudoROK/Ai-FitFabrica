import type { SimilarSearchClickAnalyticsResponse } from "@/lib/api/business-catalog-contracts";
import { getStatusBadgeTone } from "./model";
import type { BulkOperationDetails, ProductReviewSummary } from "./types";

export function StatusPanel({ message, title }: { message: string; title: string }) {
  return (
    <div className="site-card p-8">
      <p className="eyebrow">{title}</p>
      <p className="workspace-body mt-4">{message}</p>
    </div>
  );
}

export function SimilarSearchAnalyticsPanel({ analytics }: { analytics: SimilarSearchClickAnalyticsResponse }) {
  return (
    <section className="site-card mb-8 p-6">
      <p className="eyebrow">Similar Search Analytics</p>
      <h2 className="workspace-card-title mt-3">Free search click performance</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <MetricCard label="Total clicks" value={analytics.summary.total_clicks} />
        <MetricCard label="External redirects" value={analytics.summary.redirect_clicks} />
        <MetricCard label="Local-only clicks" value={analytics.summary.local_only_clicks} />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <AnalyticsList items={analytics.top_products} title="Top products" />
        <AnalyticsList items={analytics.top_marketplaces} title="Top marketplaces" />
        <AnalyticsList items={analytics.top_cities} title="Top cities" />
      </div>
    </section>
  );
}

export function ReviewQueueSummaryPanel({ summary }: { summary: ProductReviewSummary }) {
  return (
    <section className="site-card p-6">
      <p className="eyebrow">Review queue summary</p>
      <h2 className="workspace-card-title mt-3">Admin workload</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Total pending" value={summary.total} />
        <MetricCard label="Ready to approve" value={summary.readyToApprove} />
        <MetricCard label="Needs AI validation" value={summary.needsAiValidation} />
        <MetricCard label="Blocked by category" value={summary.blockedByCategory} />
        <MetricCard label="Indexing issues" value={summary.indexingIssues} />
      </div>
    </section>
  );
}

export function AdminOperationOrderPanel() {
  return (
    <section className="site-card p-6">
      <p className="eyebrow">Admin operation order</p>
      <h2 className="workspace-card-title mt-3">Safe catalog review sequence</h2>
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <InstructionCard
          title="1. Run AI validation batch"
          body="Validate product photos against declared categories before any approval action."
        />
        <InstructionCard
          title="2. Approve matched batch"
          body="Approve only products with matched category validation. Do not approve mismatched or uncertain products."
        />
        <InstructionCard
          title="3. Check indexing status"
          body="Products should move to indexed after worker processing. Retry only failed indexing records."
        />
      </div>
    </section>
  );
}

export function BulkOperationDetailsPanel({ details, onClear }: { details: BulkOperationDetails; onClear: () => void }) {
  const operationLabel =
    details.operation === "category_validation" ? "category validation batch" : "approve matched batch";
  return (
    <section className="site-card p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="eyebrow">Bulk operation details</p>
          <h2 className="workspace-card-title mt-3">{operationLabel}</h2>
        </div>
        <button
          className="rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold"
          onClick={onClear}
          type="button"
        >
          Clear bulk result
        </button>
      </div>
      {details.items.length === 0 ? (
        <p className="workspace-body mt-4">No product_id items were returned for this operation.</p>
      ) : null}
      <div className="mt-5 grid gap-3">
        {details.items.map((item) => (
          <div
            className="rounded-[18px] border border-[var(--border)] bg-white/75 p-4"
            key={`${details.operation}-${item.product_id}`}
          >
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <p className="text-sm font-semibold text-[var(--text-primary)]">product_id: {item.product_id}</p>
              <StatusBadge value={item.status} />
            </div>
            {item.error_message ? <p className="workspace-error mt-2">error_message: {item.error_message}</p> : null}
          </div>
        ))}
      </div>
    </section>
  );
}

export function StatusBadge({ label, value }: { label?: string; value: string }) {
  return (
    <span
      className={`inline-flex w-fit items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold ${getStatusBadgeTone(value)}`}
    >
      {label ? <span>{label}:</span> : null}
      <span>{value}</span>
    </span>
  );
}

function InstructionCard({ body, title }: { body: string; title: string }) {
  return (
    <div className="rounded-[22px] border border-[var(--border)] bg-white/75 p-4">
      <p className="text-sm font-semibold text-[var(--text-primary)]">{title}</p>
      <p className="workspace-body mt-2">{body}</p>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-[22px] border border-[var(--border)] bg-white/75 p-4">
      <p className="workspace-meta">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-[var(--text-primary)]">{value.toLocaleString("ru-RU")}</p>
    </div>
  );
}

function AnalyticsList({ items, title }: { items: SimilarSearchClickAnalyticsResponse["top_products"]; title: string }) {
  return (
    <div className="rounded-[22px] border border-[var(--border)] bg-white/75 p-4">
      <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">{title}</h3>
      {items.length === 0 ? <p className="workspace-meta mt-4">No click data yet.</p> : null}
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div className="flex items-start justify-between gap-3" key={`${title}-${item.key}`}>
            <p className="text-sm font-semibold text-[var(--text-primary)]">{item.label}</p>
            <p className="rounded-full bg-[var(--surface-alt)] px-3 py-1 text-xs font-semibold text-[var(--text-primary)]">
              {item.click_count}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
