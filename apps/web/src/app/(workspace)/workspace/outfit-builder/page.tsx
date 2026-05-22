import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceOutfitBuilderPage() {
  return (
    <main className="px-8 py-10 lg:px-16">
      <div className="flex items-start justify-between gap-6">
        <div><h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.6rem,6vw,5.4rem)] font-bold tracking-[-0.06em]">Подбор образа</h1><p className="mt-3 text-[1.4rem] text-[var(--text-secondary)]">Загрузите базовую вещь, и AI соберет идеальный лук.</p></div>
        <span className="rounded-full bg-[#ebe6ff] px-6 py-4 text-[1.2rem] font-semibold text-[var(--ai)]">AI Ready</span>
      </div>
      <section className="mt-10 grid gap-8 xl:grid-cols-[360px_1fr]">
        <div className="grid gap-8">
          <article className="border border-[var(--border)] bg-[var(--surface)] p-8"><h2 className="text-[2rem] font-semibold">Базовая вещь</h2><div className="mt-8 rounded-[2rem] border-2 border-dashed border-[#d8c3a5] bg-white p-12 text-center text-[1.3rem]">Загрузить фото вещи<br />JPEG, PNG до 10MB</div></article>
          <article className="border border-[var(--border)] bg-[var(--surface)] p-8"><h2 className="text-[2rem] font-semibold">Параметры подбора</h2><div className="mt-8 grid gap-6"><select className="site-select appearance-none"><option>Повседневный</option></select><select className="site-select appearance-none"><option>Весна / Осень</option></select><select className="site-select appearance-none"><option>Масс-маркет</option></select></div></article>
          <SiteButton className="w-full" icon="auto_fix_high" variant="violet">Сгенерировать образы</SiteButton>
        </div>
        <div>
          <div className="mb-6 flex items-center justify-between"><h2 className="font-[family-name:var(--font-manrope)] text-[4rem] font-bold tracking-[-0.06em]">Результаты AI</h2><span className="text-[1.4rem] text-[var(--text-muted)]">3 варианта найдено</span></div>
          <article className="site-card grid gap-6 p-6 lg:grid-cols-[0.9fr_1fr]"><ImagePlaceholder className="h-[400px]" chips={["Match 98%"]} /><div className="flex flex-col justify-between"><div><h3 className="font-[family-name:var(--font-manrope)] text-[4rem] font-bold leading-[0.95] tracking-[-0.05em]">Классический беж</h3><div className="mt-8 grid gap-5 text-[1.35rem]"><div className="flex justify-between border-b border-[var(--border)] pb-3"><span>Тренч оверсайз</span><strong>База</strong></div><div className="flex justify-between border-b border-[var(--border)] pb-3"><span>Шелковая блуза</span><strong>12 400 ₽</strong></div><div className="flex justify-between"><span>Брюки палаццо</span><strong>8 900 ₽</strong></div></div></div><SiteButton className="mt-8" href="/workspace/similar" icon="search" variant="secondary">Найти похожее</SiteButton></div></article>
          <div className="mt-6 grid gap-6 lg:grid-cols-2"><article className="site-card overflow-hidden"><ImagePlaceholder className="h-[350px] rounded-none" chips={["Match 85%"]} /><div className="p-6"><h3 className="text-[2rem] font-semibold">Smart Casual</h3><div className="mt-4 grid gap-3 text-[1.2rem]"><div className="flex justify-between"><span>Деним</span><strong>5 500 ₽</strong></div><div className="flex justify-between"><span>Базовая футболка</span><strong>2 000 ₽</strong></div></div><SiteButton className="mt-6 w-full" href="/workspace/similar" variant="secondary">Найти похожее</SiteButton></div></article><article className="site-card overflow-hidden"><ImagePlaceholder className="h-[350px] rounded-none" chips={["Match 82%"]} /><div className="p-6"><h3 className="text-[2rem] font-semibold">Вечерний акцент</h3><div className="mt-4 grid gap-3 text-[1.2rem]"><div className="flex justify-between"><span>Платье-комбинация</span><strong>9 200 ₽</strong></div><div className="flex justify-between"><span>Аксессуары</span><strong>3 500 ₽</strong></div></div><SiteButton className="mt-6 w-full" href="/workspace/similar" variant="secondary">Найти похожее</SiteButton></div></article></div>
        </div>
      </section>
    </main>
  );
}
