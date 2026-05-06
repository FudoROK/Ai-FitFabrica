import { ButtonLink } from "@/components/ui/button-link";
import { VisualPlaceholder } from "@/components/ui/visual-placeholder";
import type { PublicPageContent } from "@/types/site";

type PublicPageProps = {
  content: PublicPageContent;
};

export function PublicPage({ content }: PublicPageProps) {
  return (
    <main className="public-page">
      <section className="page-shell hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">{content.eyebrow}</p>
          <h1 className="hero-title">{content.title}</h1>
          <p className="hero-lead">{content.lead}</p>
          <div className="button-row">
            {content.actions.map((action) => (
              <ButtonLink action={action} key={`${content.title}-${action.href}-${action.label}`} />
            ))}
          </div>
          <div className="metric-grid">
            {content.metrics.map((metric) => (
              <article className="surface-subcard metric-card" key={`${content.title}-${metric.label}`}>
                <span className="metric-label">{metric.label}</span>
                <strong className="metric-value">{metric.value}</strong>
              </article>
            ))}
          </div>
        </div>
        <VisualPlaceholder data={content.placeholder} />
      </section>

      <section className="page-shell section-shell">
        <div className="section-heading">
          <p className="eyebrow">Что получает пользователь</p>
          <h2 className="section-title">Крупные блоки вместо шумной сетки</h2>
        </div>
        <div className="feature-grid">
          {content.highlights.map((section) => (
            <article className="surface-card feature-card" key={`${content.title}-${section.title}`}>
              <h3>{section.title}</h3>
              <p>{section.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="page-shell section-shell story-grid">
        <div className="surface-card story-card">
          <p className="eyebrow">Сценарий продукта</p>
          <h2 className="section-title">Идея → результат → действие</h2>
          <div className="step-list">
            {content.steps.map((step, index) => (
              <article className="step-row" key={`${content.title}-${step.title}`}>
                <span className="step-index">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.body}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
        <VisualPlaceholder compact data={content.placeholder} />
      </section>

      <section className="page-shell section-shell">
        <div className="cta-panel">
          <div>
            <p className="eyebrow">Следующий шаг</p>
            <h2 className="section-title">{content.cta.title}</h2>
            <p className="section-copy">{content.cta.body}</p>
          </div>
          <ButtonLink action={content.cta.action} />
        </div>
      </section>
    </main>
  );
}
