import { ButtonLink } from "@/components/ui/button-link";
import { VisualPlaceholder } from "@/components/ui/visual-placeholder";
import type { WorkspacePageContent } from "@/types/site";

type WorkspacePageProps = {
  content: WorkspacePageContent;
};

export function WorkspacePage({ content }: WorkspacePageProps) {
  return (
    <main className="workspace-page">
      <section className="workspace-hero">
        <div className="hero-copy">
          <p className="eyebrow">{content.eyebrow}</p>
          <h1 className="hero-title workspace-title">{content.title}</h1>
          <p className="hero-lead workspace-lead">{content.lead}</p>
          <div className="button-row">
            {content.actions.map((action) => (
              <ButtonLink action={action} key={`${content.title}-${action.href}-${action.label}`} />
            ))}
          </div>
        </div>
        <div className="workspace-status-grid">
          {content.status.map((item) => (
            <article className="surface-subcard status-card" key={`${content.title}-${item.label}`}>
              <span className="metric-label">{item.label}</span>
              <strong className="metric-value">{item.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="workspace-main-grid">
        <VisualPlaceholder data={content.placeholder} />
        <aside className="surface-card ai-panel">
          <p className="eyebrow">AI и статусы</p>
          <h2 className="section-title">Контрольный список экрана</h2>
          <div className="step-list compact-step-list">
            {content.checklist.map((section, index) => (
              <article className="step-row" key={`${content.title}-${section.title}`}>
                <span className="step-index">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{section.title}</h3>
                  <p>{section.body}</p>
                </div>
              </article>
            ))}
          </div>
        </aside>
      </section>

      <section className="panel-grid">
        {content.panels.map((panel) => (
          <article className="surface-card feature-card" key={`${content.title}-${panel.title}`}>
            <h2>{panel.title}</h2>
            <p>{panel.body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
