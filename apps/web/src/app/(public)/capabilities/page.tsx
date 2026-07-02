import { SiteButton } from "@/components/site/site-button";

const groups = [
  {
    title: "Для себя",
    items: [
      [
        "Умная примерка",
        "Проверьте, как вещь выглядит на вас, и получите аккуратный результат без декоративной генерации ради генерации."
      ],
      [
        "Стилистические рекомендации",
        "После примерки система подскажет сочетания, контекст использования и следующие шаги по образу."
      ],
      [
        "Поиск альтернатив",
        "Если вещь не подходит по цене, посадке или стилю, workflow продолжается в поиск похожих вариантов."
      ]
    ]
  },
  {
    title: "Для бизнеса",
    items: [
      [
        "Карточки товара",
        "Собирайте title, описание, атрибуты и визуальный комплект вокруг одного SKU в управляемом процессе."
      ],
      [
        "Контент-пакеты",
        "Готовьте визуалы и тексты для маркетплейсов, сайта и социальных каналов без ручной пересборки."
      ],
      [
        "Операционный контур",
        "Настраивайте бренд, правила публикации и рабочие потоки через typed workspace-панели."
      ]
    ]
  }
] as const;

export default function CapabilitiesPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container">
        <div className="rounded-[2.5rem] border border-[var(--border)] bg-[linear-gradient(135deg,#faf4ec_0%,#f4ece3_100%)] px-8 py-12 shadow-[0_28px_80px_rgba(20,20,20,0.08)] lg:px-12 lg:py-14">
          <p className="eyebrow">Возможности</p>
          <h1 className="hero-title mt-5 max-w-[860px]">Три продуктовых направления в одной системе</h1>
          <p className="hero-lead mt-6 max-w-[760px]">
            FitFabrica не сводится к одному AI-экрану. Платформа покрывает примерку, товарный контент
            и рабочие процессы бренда, а каждый маршрут продолжает предыдущий, а не обрывает его.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <SiteButton href="/workspace">Открыть workspace</SiteButton>
            <SiteButton href="/how-it-works" variant="secondary">Посмотреть flow</SiteButton>
          </div>
        </div>
      </section>

      <section className="site-container mt-16 grid gap-10">
        {groups.map((group, groupIndex) => (
          <div key={group.title}>
            <div className="flex items-end justify-between gap-6">
              <div>
                <p className="eyebrow">{groupIndex === 0 ? "B2C" : "B2B"}</p>
                <h2 className="section-title mt-3">{group.title}</h2>
              </div>
            </div>
            <div className="mt-8 grid gap-6 lg:grid-cols-3">
              {group.items.map(([title, body], index) => (
                <article
                  key={title}
                  className={`site-card p-8 ${index === 1 ? "bg-[var(--surface-alt)]" : ""}`}
                >
                  <div className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">
                    {groupIndex === 0 ? `0${index + 1}` : `1${index + 1}`}
                  </div>
                  <h3 className="workspace-card-title mt-4">{title}</h3>
                  <p className="public-body mt-4">{body}</p>
                </article>
              ))}
            </div>
          </div>
        ))}
      </section>
    </main>
  );
}
