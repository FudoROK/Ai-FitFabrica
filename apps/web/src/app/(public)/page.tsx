import Image from "next/image";
import { SiteButton } from "@/components/site/site-button";

const scenarios = [
  {
    label: "Для себя",
    title: "Персональный AI-стилист",
    body: "Примеряйте одежду на себе, проверяйте посадку и получайте честный совет: подходит ли вещь по фасону, цвету и стилю. AI FitFabrica поможет собрать образ и найти похожие варианты дешевле.",
    bullets: [
      "Виртуальная примерка на вашем фото",
      "Советы по стилю, цвету и посадке",
      "Поиск похожих вещей и выгодных альтернатив"
    ]
  },
  {
    label: "Для бизнеса",
    title: "ИИ для продаж в модной индустрии",
    body: "Создавайте карточки товаров, фото на модели и контент для маркетплейсов без дорогих съёмок. ИИ-агенты помогут улучшить визуал, описание, цену и подачу товара.",
    bullets: [
      "Карточки товаров и фото на модели",
      "Контент для маркетплейсов и соцсетей",
      "Анализ конкурентов, цены и трендов"
    ]
  }
];

export default function HomePage() {
  return (
    <main className="pb-20 pt-12 lg:pb-28">
      <section className="site-container">
        <div className="relative overflow-hidden rounded-[2.75rem] border border-[var(--border)] bg-[linear-gradient(135deg,#f8f2e9_0%,#f6efe6_55%,#efe7dd_100%)] px-7 py-10 shadow-[0_28px_80px_rgba(20,20,20,0.08)] lg:px-12 lg:py-14">
          <div aria-hidden="true" className="absolute left-[-120px] top-[-120px] h-[260px] w-[260px] rounded-full bg-[#efe4d4] blur-3xl" />
          <div aria-hidden="true" className="absolute bottom-[-120px] right-[-80px] h-[260px] w-[260px] rounded-full bg-[rgba(110,86,207,0.12)] blur-3xl" />

          <div className="relative grid items-center gap-10 lg:grid-cols-[1.02fr_0.98fr] lg:gap-14">
            <div className="max-w-[760px] text-left">
              <p className="eyebrow">AI FitFabrica</p>
              <h1 className="hero-title mt-5">ИИ-команда для одежды, покупок и продаж в модной индустрии</h1>
              <p className="hero-lead mt-6 max-w-[700px]">Виртуальная примерка, создание уникального контента и интеллектуальный анализ стиля в один клик. Переосмыслите свой гардероб или масштабируйте модный бизнес.</p>
              <div className="mt-8 flex flex-wrap gap-4">
                <SiteButton href="/for-you">Для себя</SiteButton>
                <SiteButton href="/business" variant="secondary">Для бизнеса</SiteButton>
              </div>
            </div>

            <div className="grid gap-6 lg:relative lg:block lg:h-[560px] lg:max-w-[620px] lg:pl-4">
              <article className="media-zoom site-card overflow-hidden bg-[var(--surface)] shadow-[0_28px_80px_rgba(20,20,20,0.12)] transition-transform duration-300 lg:absolute lg:left-0 lg:top-0 lg:z-10 lg:w-[72%] lg:rotate-[-6deg] lg:hover:z-30 lg:hover:translate-y-[-10px] lg:hover:rotate-[-3deg]">
                <div className="relative aspect-[3/4] bg-[#f4ede0]">
                  <Image alt="For-you fashion workflow preview" className="media-zoom-media object-cover" fill priority sizes="(min-width: 1024px) 44vw, 100vw" src="/images/home/images/home-for-you.webp" />
                </div>
              </article>

              <article className="media-zoom site-card overflow-hidden bg-[var(--surface)] shadow-[0_28px_80px_rgba(20,20,20,0.12)] transition-transform duration-300 lg:absolute lg:right-0 lg:top-[70px] lg:z-20 lg:w-[72%] lg:rotate-[6deg] lg:hover:z-30 lg:hover:translate-y-[-10px] lg:hover:rotate-[3deg]">
                <div className="relative aspect-[3/4] bg-[#f4ede0]">
                  <Image alt="Business fashion workflow preview" className="media-zoom-media object-cover" fill priority={false} sizes="(min-width: 1024px) 44vw, 100vw" src="/images/home/images/home-business.webp" />
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <div aria-hidden="true" className="h-[50px]" />

      <section className="site-container grid gap-8 lg:grid-cols-2">
        {scenarios.map((scenario, index) => (
          <article className={`site-card p-10 ${index === 1 ? "bg-[var(--surface-alt)]" : ""}`} key={scenario.title}>
            <div className="flex h-full flex-col">
              <div className="flex min-h-[74px] items-center gap-4">
                <Image
                  alt={scenario.label}
                  className="h-10 w-10 shrink-0"
                  height={40}
                  src={index === 0 ? "/images/home/icons/person-standing.svg" : "/images/home/icons/shopping-bag.svg"}
                  width={40}
                />
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--text-muted)]">{scenario.label}</p>
              </div>
              <h2 className="mt-5 min-h-[88px] workspace-card-title">
                {scenario.title}
              </h2>
              <p className="public-body mt-4 min-h-[188px]">{scenario.body}</p>
              <div className="mt-8 grid gap-3 text-[1rem] text-[var(--text-secondary)]">
                {scenario.bullets.map((bullet) => (
                  <div className="flex items-center gap-3" key={bullet}>
                    <Image alt="" aria-hidden="true" className="h-[1.1rem] w-[1.1rem] shrink-0" height={18} src="/images/home/icons/check.svg" width={18} />
                    <span>{bullet}</span>
                  </div>
                ))}
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="site-container mt-36 text-center">
        <h2 className="section-title">
          Готовы изменить свой стиль?
        </h2>
        <p className="public-body mx-auto mt-4 max-w-[920px] lg:whitespace-nowrap">
          Загрузите свое фото и начните виртуальную примерку прямо сейчас.
        </p>
        <SiteButton className="mt-10" href="/workspace/new-fitting" variant="violet">
          Начать примерку
        </SiteButton>
      </section>
    </main>
  );
}





