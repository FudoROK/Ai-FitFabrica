"use client";

type WorkspaceCapabilitySummaryItem = {
  body: string;
  title: string;
};

type WorkspaceCapabilitySummaryPanelProps = {
  publishVerdict?: string;
  summaryItems: WorkspaceCapabilitySummaryItem[];
  title: string;
};

export function WorkspaceCapabilitySummaryPanel({
  publishVerdict = "",
  summaryItems,
  title,
}: WorkspaceCapabilitySummaryPanelProps) {
  return (
    <article className="site-card p-7 lg:p-8">
      <h2 className="workspace-section-title">{title}</h2>
      <div className="mt-6 grid gap-4">
        {summaryItems.map((item) => (
          <div className="rounded-[1.5rem] border border-[var(--border)] p-5" key={item.title}>
            <p className="workspace-card-title">{item.title}</p>
            <p className="workspace-body mt-3">{item.body}</p>
          </div>
        ))}
        {publishVerdict ? (
          <div className="rounded-[1.5rem] border border-[var(--border)] p-5">
            <p className="workspace-card-title">Server verdict</p>
            <p className="workspace-body mt-3">{publishVerdict}</p>
          </div>
        ) : null}
      </div>
    </article>
  );
}
