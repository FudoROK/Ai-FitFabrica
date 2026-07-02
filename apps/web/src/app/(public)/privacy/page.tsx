import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { MaterialIcon } from "@/components/site/material-icon";

export default function PrivacyPage() {
  return (
    <main className="bg-[#fcfbf8] pb-20 pt-12">
      <section className="site-container text-center">
        <div className="eyebrow mx-auto inline-flex items-center gap-3 rounded-full bg-[#eee7e4] px-6 py-4 text-[var(--text-secondary)]">
          <MaterialIcon name="lock" />
          <span>Доверие и контроль</span>
        </div>
        <h1 className="hero-title mx-auto mt-8 max-w-[900px]">Приватность и безопасность</h1>
        <p className="hero-lead mx-auto mt-6 max-w-[860px]">
          FitFabrica проектируется как backend-first система, где пользовательские данные,
          изображения и рабочие статусы не должны разъезжаться по случайным клиентским слоям.
        </p>
      </section>

      <section className="site-container mt-20 grid gap-6 lg:grid-cols-[1.7fr_0.8fr]">
        <article className="site-card p-9">
          <p className="inline-flex rounded-full bg-[var(--success-soft)] px-5 py-2 text-sm font-semibold text-[var(--success)]">
            Строго конфиденциально
          </p>
          <h2 className="section-title mt-8">Использование фото</h2>
          <p className="public-body mt-4">
            Загруженные изображения используются только в рамках продуктового workflow:
            примерка, анализ, подготовка результата и связанные проверки качества. По архитектуре
            проекта такие действия должны идти через backend, а не через хаотичные клиентские вызовы.
          </p>
        </article>

        <article className="site-card bg-[var(--surface-alt)] p-9">
          <h2 className="section-title">Хранение данных</h2>
          <p className="public-body mt-4">
            Служебные данные, статусы и артефакты должны храниться в контролируемых backend-слоях.
            Frontend показывает состояние, но не является источником истины для профилей, кредитов
            или результатных данных.
          </p>
        </article>
      </section>

      <section className="site-container mt-10">
        <div className="overflow-hidden rounded-[2.75rem] bg-[#111015] px-8 py-10 text-white lg:grid lg:grid-cols-[0.9fr_1fr] lg:gap-12">
          <div>
            <h2 className="section-title text-white">Безопасность уровня enterprise</h2>
            <p className="workspace-body mt-6 text-white/75">
              Ключевой принцип FitFabrica: бизнес-логика, AI workflow, credits logic и публикационные
              решения остаются на backend. Это снижает риск случайного раскрытия данных и делает
              поведение системы проверяемым.
            </p>
          </div>
          <ImagePlaceholder accent="dark" className="mt-10 h-[320px] lg:mt-0" />
        </div>
      </section>
    </main>
  );
}
