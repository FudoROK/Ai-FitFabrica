import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

const quickActions = [
  ["Новая примерка", "Виртуальная примерка одежды"],
  ["Подобрать образ", "AI-стилист соберет лук по вашему"],
  ["Найти похожее", "Поиск аналогичных"],
  ["Создать карточку", "Генерация фото для"]
];

export default function WorkspaceDashboardPage() {
  return (
    <main className="px-8 py-10 lg:px-20">
      <div className="flex flex-wrap items-start justify-between gap-8">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(4rem,7vw,5.8rem)] font-bold leading-[0.94] tracking-[-0.06em]">Доброе утро, Анна</h1>
          <p className="mt-3 text-[1.5rem] text-[var(--text-secondary)]">Готовы создавать новые образы?</p>
        </div>
        <div className="border border-[var(--border)] bg-[var(--surface)] px-8 py-6">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--text-secondary)]">Баланс кредитов</p>
          <div className="mt-3 flex items-center gap-8"><strong className="text-[3.8rem] font-semibold tracking-[-0.05em]">1,240</strong><SiteButton href="/workspace/credits" variant="soft">Пополнить</SiteButton></div>
        </div>
      </div>

      <section className="mt-14 grid gap-6 xl:grid-cols-4">
        {quickActions.map(([title, body]) => (
          <article className="site-card p-8" key={title}>
            <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold leading-[0.98] tracking-[-0.05em]">{title}</h2>
            <p className="mt-4 text-[1.15rem] leading-8 text-[var(--text-secondary)]">{body}</p>
          </article>
        ))}
      </section>

      <section className="mt-16">
        <div className="flex items-end justify-between gap-4">
          <h2 className="font-[family-name:var(--font-manrope)] text-[4rem] font-bold tracking-[-0.06em]">Последние генерации</h2>
          <span className="text-[1.15rem] text-[var(--text-secondary)]">Смотреть все →</span>
        </div>
        <div className="mt-8 grid gap-7 xl:grid-cols-[1fr_1fr_0.95fr]">
          <article className="site-card overflow-hidden"><ImagePlaceholder className="h-[440px] rounded-none" chips={["Готово"]} /><div className="p-6"><h3 className="text-[1.7rem] font-semibold">Осеннее пальто (желтое)</h3><div className="mt-4 flex gap-3 text-sm text-[var(--text-muted)]"><span>Примерка</span><span>Street Style</span></div></div></article>
          <article className="site-card overflow-hidden"><ImagePlaceholder className="h-[440px] rounded-none" chips={["Готово"]} /><div className="p-6"><h3 className="text-[1.7rem] font-semibold">Вечернее платье (Шелк)</h3><div className="mt-4 flex gap-3 text-sm text-[var(--text-muted)]"><span>Карточка товара</span><span>Studio</span></div></div></article>
          <article className="site-card flex flex-col justify-between bg-[#f1eef8] p-8"><div className="mx-auto mt-20 h-24 w-24 rounded-full border-4 border-[var(--ai)] border-r-transparent" /><div><h3 className="font-[family-name:var(--font-manrope)] text-[2.1rem] font-bold tracking-[-0.04em]">Генерация образа</h3><p className="mt-4 text-[1.15rem] leading-8 text-[var(--text-secondary)]">Нейросеть обрабатывает текстуру ткани и подбирает освещение...</p></div><div><div className="mt-8 h-2 rounded-full bg-[#ded6cb]"><div className="h-2 w-3/4 rounded-full bg-[var(--ai)]" /></div><p className="mt-3 text-right text-[1.8rem] font-semibold text-[var(--ai)]">75%</p></div></article>
        </div>
      </section>
    </main>
  );
}
