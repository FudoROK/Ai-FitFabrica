import type { AdminMarketplaceDiscoveryCandidate } from "@/lib/api/business-catalog-contracts";
import { StatusBadge } from "./shared-panels";
import type { DiscoveryCandidateFilters as DiscoveryCandidateFilterState } from "./types";

export function DiscoveryCandidateReviewPanel({
  candidates,
  filters,
  onArchive,
  onApprove,
  onFiltersChange,
  onReject,
  onReload,
  rejectReasons,
  setRejectReasons,
  submittingCandidateId,
}: {
  candidates: AdminMarketplaceDiscoveryCandidate[];
  filters: DiscoveryCandidateFilterState;
  onArchive: (candidateId: string) => void;
  onApprove: (candidateId: string) => void;
  onFiltersChange: (filters: DiscoveryCandidateFilterState) => void;
  onReject: (candidateId: string) => void;
  onReload: () => void;
  rejectReasons: Record<string, string>;
  setRejectReasons: (value: Record<string, string>) => void;
  submittingCandidateId: string | null;
}) {
  return (
    <section className="site-card p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="eyebrow">Discovery Candidates</p>
          <h2 className="workspace-card-title mt-3">Marketplace candidate review</h2>
          <p className="workspace-body mt-3 max-w-[760px]">
            Review marketplace candidates discovered from approved search sources before they can become catalog inputs.
          </p>
        </div>
        <button
          className="rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold"
          onClick={onReload}
          type="button"
        >
          Reload candidates
        </button>
      </div>

      <DiscoveryCandidateFilters filters={filters} onFiltersChange={onFiltersChange} onReload={onReload} />

      {candidates.length === 0 ? (
        <div className="mt-5 rounded-[22px] border border-[var(--border)] bg-white/75 p-5">
          <p className="workspace-body">No discovery candidates match the current filters.</p>
        </div>
      ) : null}

      <div className="mt-5 grid gap-4">
        {candidates.map((candidate) => {
          const isSubmitting = submittingCandidateId === candidate.candidate_id;
          const displayTitle = candidate.title || candidate.name || candidate.source_title;
          return (
            <article className="rounded-[24px] border border-[var(--border)] bg-white/75 p-5" key={candidate.candidate_id}>
              <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap gap-2">
                    <StatusBadge value={candidate.status} />
                    <StatusBadge label="source" value={candidate.source_type} />
                    {candidate.platform_hint ? <StatusBadge label="platform" value={candidate.platform_hint} /> : null}
                  </div>
                  <h3 className="workspace-card-title mt-3 break-words">{displayTitle}</h3>
                  <p className="workspace-body mt-2 break-words">
                    source_url:{" "}
                    <a
                      className="font-semibold text-[var(--text-primary)] underline"
                      href={candidate.source_url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {candidate.source_url}
                    </a>
                  </p>
                  <div className="mt-4 grid gap-2 text-sm text-[var(--text-muted)] md:grid-cols-2 xl:grid-cols-4">
                    <p>
                      Brand: <strong>{candidate.brand || "unknown"}</strong>
                    </p>
                    <p>
                      Category: <strong>{candidate.category || "unknown"}</strong>
                    </p>
                    <p>
                      City: <strong>{candidate.city || "unknown"}</strong>
                    </p>
                    <p>
                      Price:{" "}
                      <strong>
                        {candidate.price_amount != null
                          ? `${candidate.price_amount.toLocaleString("ru-RU")} ${candidate.currency || ""}`
                          : "unknown"}
                      </strong>
                    </p>
                  </div>
                  {candidate.source_snippet ? <p className="workspace-body mt-3">{candidate.source_snippet}</p> : null}
                  {candidate.rejection_reason ? (
                    <p className="workspace-error mt-3">Rejection reason: {candidate.rejection_reason}</p>
                  ) : null}
                </div>
                <div className="grid gap-2 sm:grid-cols-3 xl:min-w-[320px] xl:grid-cols-1">
                  <button
                    className="rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
                    disabled={isSubmitting || candidate.status === "approved"}
                    onClick={() => onApprove(candidate.candidate_id)}
                    type="button"
                  >
                    Approve
                  </button>
                  <button
                    className="rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                    disabled={isSubmitting || candidate.status === "archived"}
                    onClick={() => onArchive(candidate.candidate_id)}
                    type="button"
                  >
                    Archive
                  </button>
                  <button
                    className="rounded-full border border-rose-200 px-5 py-3 text-sm font-semibold text-rose-800 disabled:cursor-not-allowed disabled:opacity-40"
                    disabled={isSubmitting || candidate.status === "rejected"}
                    onClick={() => onReject(candidate.candidate_id)}
                    type="button"
                  >
                    Reject
                  </button>
                </div>
              </div>
              <label className="mt-4 grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                Reject reason
                <input
                  className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 outline-none"
                  onChange={(event) =>
                    setRejectReasons({
                      ...rejectReasons,
                      [candidate.candidate_id]: event.target.value,
                    })
                  }
                  placeholder="Not a product page, duplicate account, unavailable source"
                  value={rejectReasons[candidate.candidate_id] ?? ""}
                />
              </label>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function DiscoveryCandidateFilters({
  filters,
  onFiltersChange,
  onReload,
}: {
  filters: DiscoveryCandidateFilterState;
  onFiltersChange: (filters: DiscoveryCandidateFilterState) => void;
  onReload: () => void;
}) {
  return (
    <div className="mt-5 grid gap-3 rounded-[22px] border border-[var(--border)] bg-white/75 p-4 md:grid-cols-2 xl:grid-cols-[160px_220px_1fr_1fr_auto]">
      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
        Status
        <select
          className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 outline-none"
          onChange={(event) =>
            onFiltersChange({
              ...filters,
              status: event.target.value as DiscoveryCandidateFilterState["status"],
            })
          }
          value={filters.status}
        >
          <option value="all">all</option>
          <option value="pending">pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="archived">archived</option>
        </select>
      </label>
      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
        Source
        <select
          className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 outline-none"
          onChange={(event) =>
            onFiltersChange({
              ...filters,
              sourceType: event.target.value as DiscoveryCandidateFilterState["sourceType"],
            })
          }
          value={filters.sourceType}
        >
          <option value="all">all</option>
          <option value="instagram">instagram</option>
          <option value="open_web">open_web</option>
          <option value="manual">manual</option>
          <option value="search_engine_discovery">search_engine_discovery</option>
          <option value="instagram_public_discovery">instagram_public_discovery</option>
          <option value="public_web_allowed">public_web_allowed</option>
        </select>
      </label>
      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
        Category
        <input
          className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 outline-none"
          onChange={(event) => onFiltersChange({ ...filters, category: event.target.value })}
          placeholder="shirt"
          value={filters.category}
        />
      </label>
      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
        City
        <input
          className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 outline-none"
          onChange={(event) => onFiltersChange({ ...filters, city: event.target.value })}
          placeholder="Almaty"
          value={filters.city}
        />
      </label>
      <button
        className="self-end rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white"
        onClick={onReload}
        type="button"
      >
        Apply filters
      </button>
    </div>
  );
}
