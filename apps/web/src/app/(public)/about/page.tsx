import { SiteButton } from "@/components/site/site-button";

const principles = [
  {
    title: "Backend управляет workflow",
    body: "Клиентский интерфейс только отправляет данные, показывает статусы и результат. Оркестрация, credits, retry, repair и quality gates остаются на backend."
  },
  {
    title: "B2C и B2B в одном рабочем контуре",
    body: "Пользователь может начать с примерки, продолжить поиском похожих вещей, а бизнес-клиент - собрать карточку товара и контент-пакет."
  },
  {
    title: "AI работает как часть продукта",
    body: "Модели не подменяют платформу. Агенты возвращают структурированные результаты, а backend решает, что сохранять, проверять и показывать дальше."
  }
] as const;

export default function AboutPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container">
        <div className="rounded-[2.5rem] border border-[var(--border)] bg-[var(--surface)] px-8 py-12 shadow-[0_28px_80px_rgba(20,20,20,0.08)] lg:px-12 lg:py-14">
          <p className="eyebrow">О платформе</p>
          <h1 className="hero-title mt-5 max-w-[880px]">AI FitFabrica помогает принимать практичные fashion-решения</h1>
          <p className="hero-lead mt-6 max-w-[790px]">
            Это backend-first fashion-commerce платформа для примерки, товарного контента, похожих товаров и рабочих
            сценариев бренда. Главная идея простая: модели генерируют, агенты анализируют, backend управляет.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <SiteButton href="/workspace/new-fitting" variant="violet">
              Открыть примерку
            </SiteButton>
            <SiteButton href="/business" variant="secondary">
              Для бизнеса
            </SiteButton>
            <SiteButton href="/contact" variant="soft">
              Связаться
            </SiteButton>
          </div>
        </div>
      </section>

      <section className="site-container mt-16 grid gap-6 lg:grid-cols-3">
        {principles.map((principle) => (
          <article className="site-card p-8" key={principle.title}>
            <h2 className="workspace-card-title">{principle.title}</h2>
            <p className="public-body mt-4">{principle.body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
