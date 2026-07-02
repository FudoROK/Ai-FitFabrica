import Image from "next/image";
import { SiteButton } from "@/components/site/site-button";

const referenceTags = ["Пальто", "Baby cashmere", "С капюшоном", "Quiet luxury"] as const;

const aiFacts = [
  ["Категория", "Пальто"],
  ["Цвет", "Теплый бежево-тауповый"],
  ["Материал", "Baby cashmere"],
  ["Фасон", "Прямой relaxed fit"],
  ["Длина", "Удлиненное"],
  ["Капюшон", "Есть"],
  ["Застежка", "Пуговицы"],
  ["Стиль", "Quiet luxury"]
] as const;

const marketResults = [
  { name: "Kaspi", title: "Бежевое пальто с капюшоном", price: "123 000 ₸", match: "82%", badge: "kaspi" as const },
  { name: "Ozon", title: "Кашемировое пальто с капюшоном", price: "89 900 ₽", match: "78%", badge: "ozon" as const },
  { name: "Wildberries", title: "Длинное пальто с капюшоном", price: "74 500 ₽", match: "71%", badge: "wildberries" as const },
  { name: "Instagram shops", title: "Кашемировые модели Алматы", price: "от 160 000 ₸", match: "76%", badge: "instagram" as const },
  { name: "Локальные бутики", title: "Quiet luxury пальто", price: "от 180 000 ₸", match: "74%", badge: "boutique" as const }
] as const;

type MarketBadge = (typeof marketResults)[number]["badge"];

function MarketBadgeIcon({ badge }: { badge: MarketBadge }) {
  if (badge === "instagram") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[radial-gradient(circle_at_30%_30%,#feda75_0%,#fa7e1e_28%,#d62976_58%,#962fbf_80%,#4f5bd5_100%)] text-white shadow-sm">
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 fill-none stroke-current stroke-[1.9]">
          <rect x="5" y="5" width="14" height="14" rx="4" />
          <circle cx="12" cy="12" r="3.2" />
          <circle cx="16.5" cy="7.5" r="0.9" fill="currentColor" stroke="none" />
        </svg>
      </span>
    );
  }

  const styles: Record<Exclude<MarketBadge, "instagram">, string> = {
    kaspi: "bg-[#e53935] text-white",
    ozon: "bg-[#2563eb] text-white",
    wildberries: "bg-[#7c3aed] text-white",
    boutique: "border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text-primary)]"
  };

  const letters: Record<Exclude<MarketBadge, "instagram">, string> = {
    kaspi: "K",
    ozon: "O",
    wildberries: "W",
    boutique: "B"
  };

  return (
    <span className={`flex h-8 w-8 items-center justify-center rounded-full text-[0.8rem] font-semibold shadow-sm ${styles[badge]}`}>
      {letters[badge]}
    </span>
  );
}

export default function ForYouPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container">
        <div className="relative overflow-hidden rounded-[2.75rem] border border-[var(--border)] bg-[linear-gradient(135deg,#f8f2e9_0%,#f6efe6_55%,#efe7dd_100%)] px-7 py-10 shadow-[0_28px_80px_rgba(20,20,20,0.08)] lg:px-12 lg:py-14">
          <div aria-hidden="true" className="absolute left-[-120px] top-[-120px] h-[260px] w-[260px] rounded-full bg-[#efe4d4] blur-3xl" />
          <div aria-hidden="true" className="absolute bottom-[-120px] right-[-80px] h-[260px] w-[260px] rounded-full bg-[rgba(110,86,207,0.12)] blur-3xl" />

          <div className="relative grid items-center gap-12 lg:grid-cols-[0.92fr_1.08fr] lg:gap-14">
            <div>
              <p className="eyebrow">Для себя</p>
              <h1 className="hero-title mt-5">Одежда, которая подходит именно вам</h1>
              <p className="hero-lead mt-6 max-w-[520px]">
                Загрузите свое фото и проверьте, как вещь работает на вашей фигуре. FitFabrica
                показывает результат, объясняет фасон и помогает перейти к следующему шагу:
                сохранить, стилизовать или искать альтернативу.
              </p>
              <div className="mt-10 flex flex-wrap gap-4">
                <SiteButton className="whitespace-nowrap" href="/workspace/new-fitting" variant="violet">
                  Начать примерку
                </SiteButton>
                <SiteButton className="whitespace-nowrap" href="/workspace/similar-search" variant="secondary">
                  Найти похожее дешевле
                </SiteButton>
              </div>
            </div>

            <div className="relative lg:min-h-[620px]">
              <div className="group relative mx-auto aspect-[9/16] w-full max-w-[318px] overflow-hidden rounded-[2.5rem] border border-[var(--border)] bg-[var(--surface)] shadow-[0_28px_80px_rgba(20,20,20,0.12)] lg:absolute lg:bottom-0 lg:right-8">
                <div className="absolute inset-0">
                  <Image
                    alt="Blazer after preview"
                    className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.03]"
                    fill
                    priority
                    sizes="(min-width: 1024px) 52vw, 100vw"
                    src="/images/for-you/images/for-you-blazer-after.webp"
                  />
                </div>
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-black/10" />
                <div className="absolute inset-0 transition-transform duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:translate-x-full">
                  <Image
                    alt="Blazer before preview"
                    className="object-cover"
                    fill
                    sizes="(min-width: 1024px) 52vw, 100vw"
                    src="/images/for-you/images/for-you-blazer-before.webp"
                  />
                  <div className="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-[rgba(247,243,236,0.95)] via-[rgba(247,243,236,0.45)] to-transparent" />
                </div>
                <div className="absolute left-6 top-6 rounded-full bg-white/88 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--text-primary)] shadow-sm">
                  Before
                </div>
                <div className="absolute right-6 top-6 rounded-full bg-white/88 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--text-primary)] shadow-sm">
                  After
                </div>
                <div className="absolute left-1/2 top-1/2 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/70 bg-white/90 text-[var(--text-primary)] shadow-[0_12px_30px_rgba(20,20,20,0.14)] transition-transform duration-700 group-hover:scale-110">
                  <span className="text-lg font-semibold">↔</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="site-container mt-[50px]">
        <div className="max-w-[980px]">
          <p className="eyebrow text-[var(--ai)]">Как это работает</p>
          <h2 className="section-title mt-4">Премиальный образ без переплаты и без угадываний</h2>
        </div>

        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          <article className="group relative min-h-[860px] overflow-hidden rounded-[2.25rem] border border-[var(--border)] bg-[var(--surface)] shadow-[0_20px_55px_rgba(20,20,20,0.08)]">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.92),rgba(248,242,233,0.88)_52%,rgba(241,234,222,0.96))]" />
            <div className="relative flex h-full flex-col p-6">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-white/90 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--ai)] shadow-sm">01</span>
                <span className="text-sm font-medium text-[var(--text-muted)]">Референс товара</span>
              </div>
              <div className="mt-5 overflow-hidden rounded-[1.8rem] border border-white/70 bg-white shadow-[0_18px_40px_rgba(20,20,20,0.08)]">
                <div className="relative aspect-[3/4]">
                  <Image
                    alt="Luxury coat reference"
                    className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.05]"
                    fill
                    sizes="(min-width: 1024px) 33vw, 100vw"
                    src="/images/for-you/images/for-you-reference-kiri-coat.webp"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/24 via-transparent to-white/10" />
                  <div className="absolute left-4 top-4 rounded-full bg-white/88 px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[var(--text-primary)] shadow-sm">
                    Quiet luxury
                  </div>
                </div>
              </div>
              <div className="mt-5 flex-1">
                <div className="text-sm uppercase tracking-[0.16em] text-[var(--text-muted)]">Kiri Coat</div>
                <h3 className="workspace-card-title mt-1">Kiri Coat</h3>
                <p className="public-body mt-1">Baby cashmere</p>
                <p className="ui-metric-inline mt-4 text-[var(--text-primary)]">€ 6,500.00</p>
                <p className="public-body mt-3 max-w-[22ch]">Пальто с капюшоном в эстетике quiet luxury.</p>
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                {referenceTags.map((tag) => (
                  <span key={tag} className="rounded-full bg-white px-3 py-2 text-sm text-[var(--text-primary)] shadow-sm">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </article>

          <article className="group relative min-h-[860px] overflow-hidden rounded-[2.25rem] border border-[var(--border)] bg-[var(--surface)] shadow-[0_20px_55px_rgba(20,20,20,0.08)]">
            <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(242,237,229,0.97))]" />
            <div className="relative flex h-full flex-col p-6">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-[rgba(111,76,255,0.12)] px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">02</span>
                <span className="rounded-full border border-[#d9cdfc] bg-[#f3eeff] px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">
                  AI confidence 94%
                </span>
              </div>
              <div className="mt-5">
                <h3 className="workspace-card-title">Что увидел AI</h3>
              </div>
              <div className="mt-6 rounded-[1.7rem] border border-white/80 bg-white/85 p-4 shadow-[0_14px_35px_rgba(20,20,20,0.06)]">
                <ul className="grid gap-3 text-[0.98rem] text-[var(--text-primary)]">
                  {aiFacts.map(([label, value]) => (
                    <li key={label} className="flex items-start justify-between gap-4">
                      <span>{label}</span>
                      <span className="text-right text-[var(--text-secondary)]">{value}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="mt-5 rounded-[1.55rem] border border-[#dfd6ff] bg-[#f5f1ff] p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--ai)]">Важно сохранить</p>
                <p className="mt-2 text-[0.98rem] leading-7 text-[var(--text-primary)]">
                  Цвет, капюшон, пуговицы, прямой силуэт и мягкую фактуру.
                </p>
              </div>
            </div>
          </article>

          <article className="group relative min-h-[860px] overflow-hidden rounded-[2.25rem] border border-[var(--border)] bg-[var(--surface)] shadow-[0_20px_55px_rgba(20,20,20,0.08)]">
            <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(243,239,232,0.98))]" />
            <div className="relative flex h-full flex-col p-6">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-white/90 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--ai)] shadow-sm">03</span>
                <span className="text-sm font-medium text-[var(--text-muted)]">Что найдено</span>
              </div>
              <div className="mt-5">
                <h3 className="workspace-card-title">Похожие варианты дешевле</h3>
              </div>
              <div className="mt-4 grid flex-1 gap-2">
                {marketResults.map((item) => (
                  <div
                    key={item.name}
                    className="flex min-h-[72px] items-center rounded-[1.15rem] border border-white/80 bg-white/90 px-4 py-2 shadow-[0_12px_26px_rgba(20,20,20,0.05)]"
                  >
                    <div className="grid w-full grid-cols-[auto,minmax(0,1fr)_auto] items-center gap-3">
                      <MarketBadgeIcon badge={item.badge} />
                      <div className="min-w-0">
                        <p className="text-[0.68rem] uppercase leading-none tracking-[0.14em] text-[var(--ai)]">{item.name}</p>
                        <p className="mt-0.5 text-[0.88rem] font-medium leading-tight text-[var(--text-primary)]">{item.title}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[0.88rem] font-semibold leading-none text-[var(--text-primary)]">{item.price}</p>
                        <p className="mt-0.5 text-[0.68rem] uppercase leading-none tracking-[0.14em] text-[var(--text-muted)]">
                          Похожесть {item.match}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </article>
        </div>
      </section>

      <section className="site-container mt-[50px]">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-[var(--surface-alt)] p-9">
          <div className="pointer-events-none absolute inset-0">
            <Image
              alt=""
              aria-hidden="true"
              className="object-cover object-center opacity-50"
              fill
              sizes="100vw"
              src="/images/for-you/images/01.webp"
            />
          </div>
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(248,243,236,0.42),rgba(248,243,236,0.18))]" />
          <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="text-sm uppercase tracking-[0.16em] text-[var(--ai)]">AI стилист</p>
              <h2 className="mt-3 max-w-[900px] workspace-card-title">Система подскажет, подходит ли вещь и что с ней делать дальше</h2>
              <p className="public-body mt-4 max-w-[820px]">
                FitFabrica анализирует фасон, цвет, пропорции и контекст использования, чтобы
                помочь понять: стоит ли сохранять вещь, с чем ее носить и когда лучше искать
                более удачную альтернативу.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                <SiteButton href="/workspace/new-fitting">Открыть примерку</SiteButton>
                <SiteButton href="/workspace/outfit-builder" variant="secondary">Перейти к образу</SiteButton>
              </div>
            </div>
            <article className="site-card bg-white/88 p-7 backdrop-blur">
              <p className="text-sm uppercase tracking-[0.16em] text-[var(--ai)]">На что смотрим</p>
              <h3 className="workspace-card-title mt-3">Короткий чек-лист решения</h3>
              <ul className="mt-5 grid gap-3 text-[var(--text-primary)]">
                {[
                  "Подходит ли цвет",
                  "Как вещь влияет на пропорции",
                  "С чем ее сочетать",
                  "Для какого сценария она уместна",
                  "Что можно заменить",
                  "Где найти выгоднее"
                ].map((item) => (
                  <li key={item} className="rounded-[1rem] border border-[var(--border)] bg-[var(--surface)] px-4 py-3">
                    {item}
                  </li>
                ))}
              </ul>
            </article>
          </div>
        </div>
      </section>
    </main>
  );
}
