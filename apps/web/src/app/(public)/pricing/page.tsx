import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

const plans = [
  ["Начало", "Free", "Бесплатно всегда", ["10 кредитов в месяц", "Базовое качество генерации", "Стандартная очередь обработки"], "Выбрать Free", "secondary"],
  ["Энтузиаст", "Standard", "₽490 / месяц", ["100 кредитов в месяц", "Высокое качество (HD)", "Приоритетная очередь", "Сохранение истории (30 дней)"], "Выбрать Standard", "primary"],
  ["Максимум", "Pro", "₽990 / месяц", ["500 кредитов в месяц", "Ультра качество (4K)", "Мгновенная генерация", "Безлимитная история"], "Выбрать Pro", "soft"]
] as const;

export default function PricingPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container text-center">
        <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.3rem,7vw,5.5rem)] font-bold leading-[0.95] tracking-[-0.06em]">Простые тарифы для любых задач</h1>
        <p className="mx-auto mt-6 max-w-[820px] text-[1.35rem] leading-8 text-[var(--text-secondary)]">Выберите план, который подходит именно вам. От бесплатных экспериментов до профессиональных решений для бизнеса.</p>
        <div className="mx-auto mt-10 flex w-fit rounded-full bg-[#e7e0dd] p-2 text-lg font-medium"><span className="rounded-full bg-white px-10 py-4">Для себя</span><span className="px-10 py-4 text-[var(--text-secondary)]">Для бизнеса</span></div>
      </section>
      <section className="site-container mt-16 grid gap-6 lg:grid-cols-3">
        {plans.map(([eyebrow, title, price, items, cta, variant], index) => (
          <article className={`site-card p-8 ${index === 1 ? "border-black" : ""}`} key={title}>
            {index === 1 ? <div className="mb-4 inline-flex rounded-full bg-black px-4 py-2 text-sm font-semibold text-white">Популярный</div> : null}
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">{eyebrow}</p>
            <h2 className="mt-4 font-[family-name:var(--font-manrope)] text-[3.6rem] font-bold tracking-[-0.05em]">{title}</h2>
            <p className="mt-2 text-[1.2rem] text-[var(--text-secondary)]">{price}</p>
            <ul className="mt-8 grid gap-4 text-[1.05rem] text-[var(--text-secondary)]">{items.map((item) => <li key={item}>{item}</li>)}</ul>
            <SiteButton className="mt-10 w-full" href="/contacts" variant={variant}>{cta}</SiteButton>
          </article>
        ))}
      </section>
      <section className="site-container mt-24">
        <div className="rounded-[2.75rem] bg-[var(--surface-alt)] p-10 lg:grid lg:grid-cols-[0.95fr_0.9fr] lg:gap-10">
          <div>
            <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">Как работают кредиты</h2>
            <p className="mt-4 max-w-[620px] text-[1.1rem] leading-8 text-[var(--text-secondary)]">Кредиты — это внутренняя валюта для оплаты работы нейросетей. Разные действия требуют разного количества кредитов в зависимости от сложности вычислений.</p>
            <div className="mt-8 grid gap-4 text-[1.05rem]"><div className="flex justify-between border-b border-[var(--border)] pb-4"><span>Примерка одной вещи</span><strong>1 кредит</strong></div><div className="flex justify-between border-b border-[var(--border)] pb-4"><span>Генерация образа целиком</span><strong>3 кредита</strong></div><div className="flex justify-between"><span>Улучшение качества (Upscale)</span><strong>2 кредита</strong></div></div>
          </div>
          <ImagePlaceholder className="mt-10 h-[280px] lg:mt-0" />
        </div>
      </section>
    </main>
  );
}
