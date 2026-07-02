import Image from "next/image";
import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

const businessMetrics = [
  { label: "Контент-пакеты", value: "15 мин" },
  { label: "Экономия на съемке", value: "до 70%" },
  { label: "Каналы публикации", value: "6+" }
] as const;

const generationPoints = [
  "Подготовка визуалов под карточку товара и каталог",
  "Единый стиль для маркетплейсов, сайта и социальных каналов",
  "Переход от артефакта к публикации без ручного хаоса"
] as const;

const contentFormats = [
  {
    title: "Посты и каталожные визуалы",
    body: "Собирайте серию материалов в одном визуальном языке бренда для запусков, сезонных подборок и промо."
  },
  {
    title: "Короткие форматы",
    body: "Готовьте вертикальные материалы и быстрые публикационные пакеты для регулярного контент-ритма."
  },
  {
    title: "Баннеры и hero-блоки",
    body: "Поддерживайте единый визуальный контур для сайта, коллекций и промо-разделов."
  }
] as const;

const trendChips = ["Oversized blazers", "Eco leather", "Cream beige", "Quiet luxury", "Capsule drops"] as const;

export default function BusinessPage() {
  return (
    <main className="flex flex-col gap-[50px] overflow-hidden pb-28 pt-10 lg:pb-36 lg:pt-16">
      <section className="site-container">
        <div className="relative overflow-hidden rounded-[2.75rem] border border-[var(--border)] bg-[linear-gradient(135deg,#f8f2e9_0%,#f6efe6_55%,#efe7dd_100%)] px-7 py-10 shadow-[0_28px_80px_rgba(20,20,20,0.08)] lg:px-12 lg:py-14">
          <div aria-hidden="true" className="absolute left-[-120px] top-[-120px] h-[260px] w-[260px] rounded-full bg-[#efe4d4] blur-3xl" />
          <div aria-hidden="true" className="absolute bottom-[-120px] right-[-80px] h-[260px] w-[260px] rounded-full bg-[rgba(110,86,207,0.12)] blur-3xl" />

          <div className="relative grid items-center gap-10 lg:grid-cols-[0.92fr_1.08fr] lg:gap-14">
            <div className="max-w-[760px]">
              <p className="eyebrow text-[var(--ai)]">Решение для бизнеса</p>
              <h1 className="hero-title mt-5 max-w-[760px]">Операционный AI-контур для fashion-команды</h1>
              <p className="hero-lead mt-6 max-w-[700px]">
                FitFabrica помогает брендам и контент-командам собирать карточки товара, визуалы,
                публикационные пакеты и рабочие AI-заметки в одном потоке вместо набора разрозненных инструментов.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                <SiteButton href="/workspace/product-card" variant="violet">
                  Открыть product workflow
                </SiteButton>
                <SiteButton href="/contacts" variant="secondary">
                  Обсудить внедрение
                </SiteButton>
              </div>

              <div className="mt-10 grid gap-4 sm:grid-cols-3">
                {businessMetrics.map((metric) => (
                  <article className="rounded-[1.75rem] border border-white/80 bg-white/72 px-5 py-5 backdrop-blur" key={metric.label}>
                    <p className="metric-label">{metric.label}</p>
                    <p className="metric-value mt-3">{metric.value}</p>
                  </article>
                ))}
              </div>
            </div>

            <div className="relative lg:min-h-[640px]">
              <article className="media-zoom site-card relative overflow-hidden bg-[var(--surface)] shadow-[0_28px_80px_rgba(20,20,20,0.12)] lg:absolute lg:left-8 lg:top-0 lg:w-[62%] lg:rotate-[-5deg]">
                <div className="relative aspect-[0.78] bg-[#ede3d4]">
                  <Image
                    alt="Business visual preview"
                    className="media-zoom-media object-cover"
                    fill
                    priority
                    sizes="(min-width: 1024px) 32vw, 100vw"
                    src="/images/business/images/business-hero.webp"
                  />
                </div>
              </article>

              <article className="site-card relative overflow-hidden border-white/70 bg-[rgba(255,253,248,0.88)] p-4 shadow-[0_22px_60px_rgba(20,20,20,0.12)] lg:absolute lg:bottom-4 lg:right-0 lg:w-[68%]">
                <div className="relative overflow-hidden rounded-[1.6rem] border border-[var(--border)] bg-[#f4ede5]">
                  <Image
                    alt="Рабочая панель FitFabrica"
                    className="h-auto w-full object-cover"
                    height={960}
                    sizes="(min-width: 1024px) 30vw, 100vw"
                    src="/images/business/images/business-workspace-screen.png"
                    width={1280}
                  />
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <span className="rounded-full bg-[var(--ai-soft)] px-4 py-2 text-sm font-semibold text-[var(--ai)]">Карточки товара</span>
                  <span className="rounded-full bg-[#f3ece3] px-4 py-2 text-sm font-semibold text-[var(--text-primary)]">AI-контент</span>
                  <span className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-[var(--text-primary)]">Операционный статус</span>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section className="site-container">
        <div className="grid gap-8 lg:grid-cols-[0.92fr_1.08fr]">
          <article className="site-card p-8 lg:p-10">
            <p className="eyebrow text-[var(--ai)]">Контент-поток</p>
            <h2 className="section-title mt-4">Материалы для каталога без тяжелого продакшна</h2>
            <p className="public-body mt-6">
              Бизнес-сценарий FitFabrica помогает перейти от исходного товара к рабочему набору материалов:
              карточка, визуал, текст, статус качества и следующий шаг публикации.
            </p>
            <ul className="public-body mt-8 grid gap-4">
              {generationPoints.map((point) => (
                <li className="flex gap-3" key={point}>
                  <span aria-hidden="true" className="mt-[0.42rem] h-2.5 w-2.5 rounded-full bg-[var(--ai)]" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </article>

          <article className="site-card overflow-hidden p-4 lg:p-5">
            <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="media-zoom relative min-h-[360px] overflow-hidden rounded-[2rem] bg-[#efe6d9]">
                <Image
                  alt="Business workflow preview"
                  className="media-zoom-media object-cover"
                  fill
                  sizes="(min-width: 1024px) 28vw, 100vw"
                  src="/images/business/images/business-hero.webp"
                />
              </div>
              <div className="grid gap-4">
                <div className="rounded-[2rem] border border-[var(--border)] bg-[var(--surface-alt)] p-6">
                  <p className="metric-label">Готовый результат</p>
                  <p className="workspace-card-title mt-3">Контент для карточки, сайта и публикации</p>
                  <p className="public-body mt-4">
                    Один исходник превращается в управляемый пакет материалов для нескольких каналов.
                  </p>
                </div>
                <ImagePlaceholder
                  accent="violet"
                  chips={["Съемка не требуется", "Единый стиль бренда"]}
                  className="min-h-[190px]"
                />
              </div>
            </div>
          </article>
        </div>
      </section>

      <section className="site-container">
        <div className="text-center">
          <h2 className="section-title">Готовые форматы контента</h2>
          <p className="public-body mx-auto mt-4 max-w-[860px]">
            Собирайте единый комплект коммерческих материалов без разрыва между каталогом, сайтом и social-каналами.
          </p>
        </div>

        <div className="mt-14 grid gap-6 lg:grid-cols-3">
          {contentFormats.map((item, index) => (
            <article
              className={`site-card p-8 ${index === 1 ? "bg-[#eee7df]" : index === 2 ? "bg-[var(--surface-alt)]" : ""}`}
              key={item.title}
            >
              <p className="eyebrow text-[var(--ai)]">Формат {index + 1}</p>
              <h3 className="workspace-card-title mt-4">{item.title}</h3>
              <p className="public-body mt-4">{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="site-container">
        <div className="rounded-[2.75rem] bg-[#e8e0d6] p-8 lg:p-12">
          <div className="grid gap-8 lg:grid-cols-[0.78fr_1.22fr] lg:gap-12">
            <article className="site-card p-8 lg:p-9">
              <p className="eyebrow text-[var(--ai)]">Рынок и стратегия</p>
              <h3 className="workspace-card-title mt-4">Контур анализа конкурентов</h3>
              <p className="public-body mt-5">
                В enterprise-сценарии этот слой помогает сравнивать позиционирование, упаковку товара
                и приоритеты публикации без ручной аналитической пересборки.
              </p>
              <div className="public-body mt-8 grid gap-4">
                <div className="flex justify-between border-b border-[var(--border)] pb-4">
                  <span>Средняя цена в категории</span>
                  <strong>Dynamic</strong>
                </div>
                <div className="flex justify-between border-b border-[var(--border)] pb-4">
                  <span>Сегмент спроса</span>
                  <strong>Backend-driven</strong>
                </div>
                <div className="flex justify-between">
                  <span>Тренд сезона</span>
                  <strong>AI-assisted</strong>
                </div>
              </div>
            </article>

            <div className="grid gap-6">
              <div>
                <p className="eyebrow text-[var(--ai)]">Прогноз трендов</p>
                <h2 className="section-title mt-4">Сигналы для продаж и контента</h2>
                <p className="public-body mt-5 max-w-[700px]">
                  Этот блок показывает, как AI- и аналитический слой может подсказывать, какие силуэты,
                  фактуры и подачи стоит усиливать в ближайшем цикле публикаций.
                </p>
              </div>

              <div className="flex flex-wrap gap-4">
                {trendChips.map((chip) => (
                  <span className="rounded-full bg-white px-5 py-3 text-sm font-semibold text-[var(--text-primary)]" key={chip}>
                    {chip}
                  </span>
                ))}
              </div>

              <div className="site-card overflow-hidden p-4">
                <div className="relative overflow-hidden rounded-[1.75rem] border border-[var(--border)] bg-[#f4ede5]">
                  <Image
                    alt="Рабочая панель FitFabrica"
                    className="h-auto w-full object-cover"
                    height={960}
                    sizes="(min-width: 1024px) 40vw, 100vw"
                    src="/images/business/images/business-workspace-screen.png"
                    width={1280}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
