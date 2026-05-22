import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceSimilarPage() {
  return (
    <main className="grid min-h-screen xl:grid-cols-[1fr_1.15fr]">
      <section className="border-r border-[var(--border)] px-10 py-10">
        <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.2rem,5vw,4.5rem)] font-bold tracking-[-0.06em]">Найти похожее</h1>
        <p className="mt-3 text-[1.25rem] leading-8 text-[var(--text-secondary)]">Загрузите референс, и наш ИИ найдет доступные аналоги.</p>
        <div className="mt-10 rounded-[3rem] border-2 border-dashed border-[#d8c3a5] bg-[var(--surface)] p-12 text-center"><div className="mx-auto h-20 w-20 rounded-full bg-[var(--surface-alt)]" /><p className="mt-8 text-[1.8rem] font-semibold">Загрузить фото вещи</p><p className="mt-2 text-[1.2rem] text-[var(--text-secondary)]">или перетащите файл сюда</p><p className="mt-2 text-[1.2rem] text-[var(--text-secondary)]">JPEG, PNG до 10MB</p></div>
        <div className="my-8 flex items-center gap-4 text-[var(--text-muted)]"><div className="h-px flex-1 bg-[var(--border)]" /><span className="text-[1.4rem] font-semibold uppercase tracking-[0.18em]">или вставьте ссылку</span><div className="h-px flex-1 bg-[var(--border)]" /></div>
        <input className="site-input" placeholder="https://..." />
        <label className="mt-8 block text-[1.2rem] font-semibold">Максимальный бюджет (₽)</label>
        <input className="site-input mt-3" placeholder="Например, 15000" />
        <SiteButton className="mt-10 w-full" icon="auto_awesome" variant="violet">Анализировать и найти</SiteButton>
        <div className="mt-12 rounded-[2.75rem] border border-[#bcaeff] bg-[#ede6ff] p-8"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">AI анализ завершен</p><div className="mt-6 grid gap-4"><div className="flex justify-between text-[1.2rem]"><span>Тип</span><strong>Жакет / Блейзер</strong></div><div className="flex justify-between text-[1.2rem]"><span>Цвет</span><strong>Бежевый</strong></div><div className="flex justify-between text-[1.2rem]"><span>Силуэт</span><strong>Оверсайз, прямой</strong></div></div></div>
      </section>
      <section className="px-10 py-10">
        <div className="flex flex-wrap items-end justify-between gap-6 border-b border-[var(--border)] pb-8">
          <div><h2 className="font-[family-name:var(--font-manrope)] text-[clamp(3.2rem,5vw,4.8rem)] font-bold tracking-[-0.06em]">Найдено 12 вариантов</h2><p className="mt-3 text-[1.2rem] text-[var(--text-secondary)]">Отсортировано по максимальному сходству</p></div>
          <span className="text-[1.3rem] font-semibold">Фильтры</span>
        </div>
        <div className="mt-10 grid gap-7 xl:grid-cols-2">
          <article className="site-card overflow-hidden border-2 border-[var(--ai)]"><ImagePlaceholder className="h-[350px] rounded-none" chips={["Лучший вариант", "94% сходство"]} /><div className="p-8"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">Mass Market Brand</p><h3 className="mt-4 font-[family-name:var(--font-manrope)] text-[2.2rem] font-bold tracking-[-0.04em]">Двубортный блейзер</h3><div className="mt-6 flex items-end justify-between"><strong className="text-[4rem] font-semibold leading-none">8 500 ₽</strong><span className="rounded-[1rem] bg-[var(--success-soft)] px-4 py-3 text-[1.1rem] font-semibold text-[var(--success)]">Выгода ~ 140 000 ₽</span></div><SiteButton className="mt-8 w-full" variant="secondary">Смотреть в магазине</SiteButton></div></article>
          <article className="site-card overflow-hidden"><ImagePlaceholder className="h-[350px] rounded-none" chips={["88% сходство"]} /><div className="p-8"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">Local Designer</p><h3 className="mt-4 font-[family-name:var(--font-manrope)] text-[2.2rem] font-bold tracking-[-0.04em]">Прямой блейзер</h3><div className="mt-6 flex items-end justify-between"><strong className="text-[4rem] font-semibold leading-none">12 900 ₽</strong><span className="rounded-[1rem] bg-[var(--surface-alt)] px-4 py-3 text-[1.1rem] font-semibold text-[var(--text-secondary)]">Выгода ~ 135 600 ₽</span></div><SiteButton className="mt-8 w-full" variant="secondary">Смотреть в магазине</SiteButton></div></article>
          <article className="site-card overflow-hidden xl:col-span-2"><ImagePlaceholder className="h-[360px] rounded-none" /><div className="p-8"><h3 className="font-[family-name:var(--font-manrope)] text-[2.4rem] font-bold tracking-[-0.04em]">Премиальная интерпретация</h3><p className="mt-4 max-w-[720px] text-[1.2rem] leading-8 text-[var(--text-secondary)]">Расширенный список аналогов с точным силуэтом и мягким кроем сохранен для следующего шага сравнения.</p></div></article>
        </div>
      </section>
    </main>
  );
}
