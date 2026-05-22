import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceTryOnResultPage() {
  return (
    <main className="px-8 py-10 lg:px-16">
      <div className="flex items-start justify-between gap-6">
        <div><h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.6rem,6vw,5.4rem)] font-bold tracking-[-0.06em]">Результат примерки</h1><p className="mt-3 text-[1.4rem] text-[var(--text-secondary)]">Идеальная посадка. Ваш новый образ готов.</p></div>
        <SiteButton variant="secondary">Сохранить</SiteButton>
      </div>
      <section className="mt-10 grid gap-8 xl:grid-cols-[1fr_330px]">
        <div>
          <ImagePlaceholder className="h-[460px]" chips={["До", "После (AI)"]} split />
          <div className="site-card mt-8 flex flex-wrap gap-4 p-6"><SiteButton variant="primary">Добавить в корзину</SiteButton><SiteButton href="/workspace/outfit-builder" icon="auto_fix_high" variant="soft">Подобрать образ</SiteButton><SiteButton href="/workspace/similar" icon="search" variant="soft">Найти похожее</SiteButton></div>
        </div>
        <div className="grid gap-8">
          <article className="rounded-[2.5rem] border border-[#c7b8ff] bg-[#ede6ff] p-8"><h2 className="font-[family-name:var(--font-manrope)] text-[2.4rem] font-bold tracking-[-0.04em] text-[#2f2570]">Анализ качества</h2><div className="mt-8 grid gap-5">{[["Посадка по фигуре", "98% Точность"], ["Рендер текстур", "Реалистично"], ["Освещение сцены", "Адаптировано"]].map(([label, value]) => <div className="rounded-[2rem] bg-white px-5 py-4 text-[1.1rem]" key={label}><strong>{label}</strong><span className="float-right text-[var(--success)]">{value}</span></div>)}</div></article>
          <article className="site-card p-8"><h2 className="font-[family-name:var(--font-manrope)] text-[2.4rem] font-bold tracking-[-0.04em]">Стилевые рекомендации</h2><div className="mt-8 grid gap-8 text-[1.1rem] leading-8 text-[var(--text-secondary)]"><div><strong className="block text-black">Цветотип</strong>Бежевый тренч отлично гармонирует с вашим теплым оттенком кожи.</div><div><strong className="block text-black">Анализ фасона</strong>Прямой крой визуально вытягивает силуэт. Рекомендуем носить в расстегнутом виде.</div><div><strong className="block text-black">С чем носить</strong>Белая рубашка, базовый топ, черные аксессуары и мягкая обувь без агрессивного декора.</div></div></article>
        </div>
      </section>
    </main>
  );
}
