import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceHistoryPage() {
  return (
    <main className="px-8 py-10 lg:px-16">
      <div className="grid gap-8 xl:grid-cols-[1fr_0.95fr]">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(4rem,7vw,6rem)] font-bold leading-[0.94] tracking-[-0.06em]">
            История и проекты
          </h1>
          <p className="mt-4 max-w-[520px] text-[1.4rem] leading-[1.55] text-[var(--text-secondary)]">
            Управление вашими генерациями и сохраненными результатами.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 self-start rounded-full border border-[var(--border)] bg-[var(--surface)] p-2 text-[1.15rem] font-medium">
          <span className="rounded-full bg-black px-8 py-4 text-white">Примерки</span>
          <span className="px-8 py-4 text-[var(--text-secondary)]">Образы</span>
          <span className="px-8 py-4 text-[var(--text-secondary)]">Похожие товары</span>
          <span className="px-8 py-4 text-[var(--text-secondary)]">Карточки</span>
        </div>
      </div>

      <section className="mt-12 grid gap-7 xl:grid-cols-3">
        <article className="site-card overflow-hidden p-6">
          <ImagePlaceholder chips={["Готово"]} className="h-[420px]" />
          <h2 className="mt-6 font-[family-name:var(--font-manrope)] text-[3rem] font-bold leading-[0.96] tracking-[-0.05em]">
            Вечерний шелк
          </h2>
          <p className="mt-3 text-[1.2rem] text-[var(--text-secondary)]">
            Генерация образа • 12 Окт 2023
          </p>
          <div className="mt-8 flex items-center gap-4">
            <SiteButton className="flex-1" variant="soft">
              Открыть
            </SiteButton>
            <button className="site-pill-button site-pill-button--icon text-2xl" type="button">
              ↓
            </button>
          </div>
        </article>

        <article className="site-card overflow-hidden p-6">
          <ImagePlaceholder chips={["В процессе"]} className="h-[420px]" />
          <h2 className="mt-6 font-[family-name:var(--font-manrope)] text-[3rem] font-bold leading-[0.96] tracking-[-0.05em]">
            Летняя капсула
          </h2>
          <p className="mt-3 text-[1.2rem] text-[var(--text-secondary)]">Примерка • 14 Окт 2023</p>
          <div className="mt-8 flex items-center gap-4">
            <SiteButton className="flex-1" variant="soft">
              Открыть
            </SiteButton>
          </div>
        </article>

        <article className="site-card overflow-hidden p-6">
          <ImagePlaceholder accent="dark" chips={["Готово"]} className="h-[420px]" />
          <h2 className="mt-6 font-[family-name:var(--font-manrope)] text-[3rem] font-bold leading-[0.96] tracking-[-0.05em]">
            Осеннее пальто
          </h2>
          <p className="mt-3 text-[1.2rem] text-[var(--text-secondary)]">
            Подбор образа • 10 Окт 2023
          </p>
          <div className="mt-8 flex items-center gap-4">
            <SiteButton className="flex-1" variant="soft">
              Открыть
            </SiteButton>
            <button className="site-pill-button site-pill-button--icon text-2xl" type="button">
              ↓
            </button>
          </div>
        </article>
      </section>
    </main>
  );
}
