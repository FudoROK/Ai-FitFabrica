import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

const plans = [
  ["Старт", "Free", "Бесплатно", ["Ознакомительный доступ", "Базовые проверки сценария", "Стандартная очередь"], "Оставить заявку", "secondary"],
  ["Команда", "Standard", "По согласованию", ["Рабочие product-потоки", "Приоритетная обработка", "История и продолжение workflow"], "Обсудить Standard", "primary"],
  ["Enterprise", "Pro", "Индивидуально", ["Расширенные лимиты", "Операционный контур для команды", "Подготовка к интеграции и масштабированию"], "Обсудить Enterprise", "soft"]
] as const;

export default function PricingPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container text-center">
        <p className="eyebrow">Pricing</p>
        <h1 className="hero-title">Простые тарифные уровни без маркетингового шума</h1>
        <p className="hero-lead mx-auto mt-6 max-w-[820px]">
          FitFabrica строится вокруг сценариев и рабочих потоков, поэтому финальная тарификация
          зависит от объема операций, типа команды и глубины интеграции, а не только от количества экранов.
        </p>
      </section>

      <section className="site-container mt-16 grid gap-6 lg:grid-cols-3">
        {plans.map(([eyebrow, title, price, items, cta, variant], index) => (
          <article className={`site-card p-8 ${index === 1 ? "border-black" : ""}`} key={title}>
            {index === 1 ? (
              <div className="mb-4 inline-flex rounded-full bg-black px-4 py-2 text-sm font-semibold text-white">
                Основной сценарий
              </div>
            ) : null}
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">{eyebrow}</p>
            <h2 className="mt-4 section-title">{title}</h2>
            <p className="public-body mt-2">{price}</p>
            <ul className="public-body mt-8 grid gap-4">
              {items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <SiteButton className="mt-10 w-full" href="/contact" variant={variant}>
              {cta}
            </SiteButton>
          </article>
        ))}
      </section>

      <section className="site-container mt-24">
        <div className="rounded-[2.75rem] bg-[var(--surface-alt)] p-10 lg:grid lg:grid-cols-[0.95fr_0.9fr] lg:gap-10">
          <div>
            <h2 className="section-title">Как работают кредиты и usage</h2>
            <p className="public-body mt-4 max-w-[620px]">
              На продуктовой стороне кредиты должны рассчитываться backend-логикой. Frontend показывает
              баланс, ожидаемую стоимость и результат списания, но не вычисляет их самостоятельно.
            </p>
            <div className="public-body mt-8 grid gap-4">
              <div className="flex justify-between border-b border-[var(--border)] pb-4">
                <span>Try-on сценарий</span>
                <strong>Usage-based</strong>
              </div>
              <div className="flex justify-between border-b border-[var(--border)] pb-4">
                <span>Product-content workflow</span>
                <strong>Usage-based</strong>
              </div>
              <div className="flex justify-between">
                <span>Enterprise интеграция</span>
                <strong>Custom</strong>
              </div>
            </div>
          </div>
          <ImagePlaceholder className="mt-10 h-[280px] lg:mt-0" />
        </div>
      </section>
    </main>
  );
}
