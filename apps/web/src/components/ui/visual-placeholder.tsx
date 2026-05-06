import type { PagePlaceholder } from "@/types/site";

type VisualPlaceholderProps = {
  compact?: boolean;
  data: PagePlaceholder;
};

export function VisualPlaceholder({
  compact = false,
  data
}: VisualPlaceholderProps) {
  return (
    <section className={`visual-panel ${compact ? "visual-panel-compact" : ""}`}>
      <div className="visual-panel-copy">
        <p className="eyebrow">{data.eyebrow}</p>
        <h2 className="visual-panel-title">{data.title}</h2>
        <p className="visual-panel-body">{data.body}</p>
      </div>
      <div className="visual-panel-stage" aria-label="Заглушка для будущего изображения">
        <div className="visual-panel-orbit visual-panel-orbit-a" />
        <div className="visual-panel-orbit visual-panel-orbit-b" />
        <div className="visual-panel-screen">
          <div className="visual-panel-screen-top">
            <span className="status-dot" />
            <span className="status-dot" />
            <span className="status-dot" />
          </div>
          <div className="visual-panel-screen-body">
            {data.items.map((item) => (
              <div className="visual-panel-item" key={`${data.title}-${item}`}>
                <span className="visual-panel-item-bar" />
                <span>{item}</span>
              </div>
            ))}
          </div>
          <div className="visual-panel-dropzone">
            <span>Вставьте сюда ваше изображение</span>
            <small>PNG, JPG, WebP</small>
          </div>
        </div>
      </div>
    </section>
  );
}
