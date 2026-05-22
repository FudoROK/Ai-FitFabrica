import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function BusinessPage() {
  return (
    <main className="pb-28 pt-16 lg:pb-36 lg:pt-20">
      <section className="site-container text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">B2B решение</p>
        <h1 className="mx-auto mt-4 max-w-[900px] font-[family-name:var(--font-manrope)] text-[clamp(3.5rem,7vw,5.8rem)] font-bold leading-[0.95] tracking-[-0.06em]">AI-команда для fashion-продаж</h1>
        <p className="mx-auto mt-6 max-w-[760px] text-[1.35rem] leading-8 text-[var(--text-secondary)]">Автоматизируйте создание визуального контента, анализируйте рынок и увеличивайте конверсию с помощью передовых нейросетей, настроенных специально для модных брендов.</p>
        <div className="mt-10 flex justify-center gap-4 lg:mt-12">
          <SiteButton href="/workspace/product-card" icon="photo_camera" variant="violet">Создать карточку товара</SiteButton>
          <SiteButton href="/contacts" variant="secondary">Запросить демо</SiteButton>
        </div>
      </section>

      <section className="site-container mt-24 lg:mt-32">
        <div className="site-card grid gap-12 p-10 lg:grid-cols-[0.85fr_1fr] lg:gap-16 lg:p-14">
          <div>
            <p className="text-sm uppercase tracking-[0.18em] text-[var(--ai)]">Генерация контента</p>
            <h2 className="mt-4 font-[family-name:var(--font-manrope)] text-[3.1rem] font-bold leading-[1] tracking-[-0.05em]">Идеальные фото на модели за секунды</h2>
            <p className="mt-6 text-[1.1rem] leading-8 text-[var(--text-secondary)]">Забудьте о дорогих фотосессиях. Загрузите фото одежды, и наша нейросеть создаст реалистичные снимки на профессиональных виртуальных моделях с учетом целевой аудитории вашего бренда.</p>
            <ul className="mt-8 grid gap-3 text-[var(--text-secondary)]">
              <li>Выбор типажа, возраста и комплекции модели</li>
              <li>Студийное освещение и реалистичные тени</li>
              <li>Автоматическая адаптация под маркетплейсы</li>
            </ul>
          </div>
          <ImagePlaceholder accent="sand" chips={["AI обработка завершена"]} className="h-[380px]" split />
        </div>
      </section>

      <section className="site-container mt-32 lg:mt-40">
        <div className="text-center"><h2 className="font-[family-name:var(--font-manrope)] text-[3.2rem] font-bold tracking-[-0.05em]">Готовые пакеты контента</h2><p className="mt-4 text-[1.2rem] text-[var(--text-secondary)]">Один клик для создания полного набора визуалов для всех ваших каналов продаж.</p></div>
        <div className="mt-14 grid gap-8 lg:mt-16 lg:grid-cols-[1.4fr_0.7fr] lg:gap-10"><article className="site-card overflow-hidden p-8"><h3 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold">Instagram Posts</h3><p className="mt-4 text-[var(--text-secondary)]">Серия гармоничных постов в едином стиле бренда.</p><ImagePlaceholder className="mt-10 h-[220px]" /></article><div className="grid gap-8 lg:gap-10"><article className="site-card bg-[#ebe7e6] p-8"><h3 className="font-semibold">Stories & Reels</h3><p className="mt-3 text-[var(--text-secondary)]">Динамичные форматы с текстом и анимацией.</p></article><article className="site-card bg-[var(--surface-alt)] p-8 text-center"><h3 className="font-semibold">Баннеры для сайта</h3><p className="mt-5 text-[var(--text-secondary)]">Широкоформатные имиджи</p></article></div></div>
      </section>

      <section className="site-container mt-32 lg:mt-40">
        <div className="rounded-[2.75rem] bg-[#e5e0de] p-10 lg:grid lg:grid-cols-[0.7fr_1fr] lg:gap-14 lg:p-14">
          <div className="site-card p-8 lg:p-9"><h3 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold">Анализ конкурентов</h3><p className="mt-5 text-sm leading-7 text-[var(--text-secondary)]">AI мониторит цены, ассортимент и визуальную подачу ваших главных конкурентов, предоставляя actionable insights для корректировки стратегии.</p><div className="mt-10 grid gap-4 text-sm"><div className="flex justify-between border-b border-[var(--border)] pb-4"><span>Средняя цена в категории</span><strong>₽ 4,500</strong></div><div className="flex justify-between"><span>Доминирующий цвет сезона</span><strong>Бургунди</strong></div></div></div>
          <div className="mt-12 lg:mt-0"><h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">Тренды для продаж</h2><p className="mt-5 max-w-[600px] text-[1.15rem] leading-8 text-[var(--text-secondary)]">Получайте предиктивную аналитику о том, какие силуэты, ткани и стилизации будут востребованы в следующем месяце.</p><div className="mt-10 flex flex-wrap gap-4">{["Оверсайз блейзеры", "Эко-кожа", "Скинни джинсы"].map((chip) => <span className="rounded-full bg-white px-4 py-2 text-sm" key={chip}>{chip}</span>)}</div></div>
        </div>
      </section>
    </main>
  );
}
