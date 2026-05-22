import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceStyleProfilePage() {
  return (
    <main className="px-8 py-10 lg:px-16">
      <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.6rem,6vw,5.6rem)] font-bold tracking-[-0.06em]">
        Персональные предпочтения
      </h1>
      <p className="mt-4 max-w-[980px] text-[1.4rem] leading-[1.6] text-[var(--text-secondary)]">
        Пожалуйста, уточните параметры вашей фигуры и вкуса. Эти данные помогут
        искусственному интеллекту подбирать образы, которые будут сидеть безупречно.
      </p>
      <div className="mt-8 inline-flex rounded-full border border-[#c5b6ff] bg-[#efe9ff] px-7 py-4 text-[1.2rem] text-[var(--ai)]">
        AI использует эти настройки для генерации точных рекомендаций
      </div>

      <section className="mt-10 grid gap-6 xl:grid-cols-[1fr_0.95fr]">
        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[2.6rem] font-bold tracking-[-0.04em]">
            Параметры фигуры
          </h2>
          <p className="mt-4 text-[1.15rem] leading-8 text-[var(--text-secondary)]">
            Укажите ваши точные мерки для идеальной посадки виртуальных моделей.
          </p>
          <div className="mt-8 grid gap-8 md:grid-cols-2">
            {[["Рост (см)", "170"], ["Грудь (см)", "90"], ["Талия (см)", "65"], ["Бедра (см)", "94"]].map(
              ([label, value]) => (
                <label
                  className="grid gap-3 text-[1rem] font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]"
                  key={label}
                >
                  <span>{label}</span>
                  <input
                    className="site-input !border-x-0 !border-t-0 !rounded-none bg-transparent px-0 text-[2rem] font-medium text-black"
                    readOnly
                    value={value}
                  />
                </label>
              )
            )}
          </div>
        </article>

        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[2.6rem] font-bold tracking-[-0.04em]">
            Предпочтения посадки
          </h2>
          <p className="mt-4 text-[1.15rem] leading-8 text-[var(--text-secondary)]">
            Как вы предпочитаете носить одежду? Это повлияет на визуализацию силуэта.
          </p>
          <div className="mt-8 grid gap-4">
            <button className="site-pill-button text-[1.2rem] font-medium" type="button">
              Приталенный (Slim)
            </button>
            <button
              className="site-pill-button text-[1.2rem] font-semibold"
              data-selected="true"
              type="button"
            >
              Стандартный (Regular)
            </button>
            <button className="site-pill-button text-[1.2rem] font-medium" type="button">
              Свободный (Oversize)
            </button>
          </div>
        </article>
      </section>

      <section className="mt-8 grid gap-6">
        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[2.6rem] font-bold tracking-[-0.04em]">
            Цветовая гамма
          </h2>
          <div className="mt-8 grid gap-8 xl:grid-cols-2">
            <div>
              <p className="text-[1.2rem] font-semibold">Любимые оттенки</p>
              <p className="mt-2 text-[var(--text-secondary)]">
                Цвета, которые мы будем предлагать чаще.
              </p>
              <div className="mt-6 flex gap-4">
                {["#000000", "#ffffff", "#5d48d6", "#dcc29a", "#2f976c"].map((color) => (
                  <span
                    className="h-16 w-16 rounded-full border border-[var(--border)]"
                    key={color}
                    style={{ backgroundColor: color }}
                  />
                ))}
                <span className="grid h-16 w-16 place-items-center rounded-full border border-dashed border-[var(--border)] text-3xl text-[var(--text-muted)]">
                  +
                </span>
              </div>
            </div>

            <div>
              <p className="text-[1.2rem] font-semibold">Желательно избегать</p>
              <p className="mt-2 text-[var(--text-secondary)]">
                Исключим эти цвета из ваших рекомендаций.
              </p>
              <div className="mt-6 flex gap-4">
                {["#e76d5b", "#636367"].map((color) => (
                  <span className="h-16 w-16 rounded-full" key={color} style={{ backgroundColor: color }} />
                ))}
                <span className="grid h-16 w-16 place-items-center rounded-full border border-dashed border-[var(--border)] text-3xl text-[var(--text-muted)]">
                  +
                </span>
              </div>
            </div>
          </div>
        </article>

        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[2.6rem] font-bold tracking-[-0.04em]">
            Ценовой сегмент
          </h2>
          <p className="mt-4 max-w-[980px] text-[1.15rem] leading-8 text-[var(--text-secondary)]">
            Комфортный для вас бюджет при подборе реальных вещей (если активирована
            функция шопинга).
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            {["Масс-маркет", "Middle", "Premium"].map((item, index) => (
              <button
                className="site-pill-button px-8 text-[1.1rem] font-medium"
                data-selected={index === 1 ? "true" : undefined}
                key={item}
                type="button"
              >
                {item}
              </button>
            ))}
          </div>
          <SiteButton className="mt-8" variant="violet">
            Сохранить настройки
          </SiteButton>
        </article>
      </section>
    </main>
  );
}
