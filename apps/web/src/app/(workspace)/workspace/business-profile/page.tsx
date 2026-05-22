import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceBusinessProfilePage() {
  return (
    <main className="px-8 py-10 lg:px-16">
      <div className="flex flex-wrap items-start justify-between gap-6 border-b border-[var(--border)] pb-8">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.8rem,6vw,5.6rem)] font-bold tracking-[-0.06em]">
            Профиль бизнеса
          </h1>
          <p className="mt-3 max-w-[860px] text-[1.35rem] leading-8 text-[var(--text-secondary)]">
            Настройте уникальный стиль и параметры вашего магазина для точной генерации
            контента.
          </p>
        </div>
        <SiteButton>Сохранить изменения</SiteButton>
      </div>

      <section className="mt-10 grid gap-6 xl:grid-cols-[1fr_0.68fr]">
        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">
            Основная информация
          </h2>
          <div className="mt-8 grid gap-6">
            <label className="grid gap-3 text-[1.2rem] font-semibold">
              <span>Название магазина или бренда</span>
              <input className="site-input" defaultValue="Urban Silk Studio" />
            </label>
            <label className="grid gap-3 text-[1.2rem] font-semibold">
              <span>Описание бренда (для контекста ИИ)</span>
              <textarea
                className="site-textarea"
                defaultValue="Современный бренд женской одежды, специализирующийся на минималистичных силуэтах и натуральных тканях. Эстетика: тихая роскошь, городской комфорт."
              />
            </label>
            <div className="border-t border-[var(--border)] pt-6">
              <div className="flex items-center gap-5">
                <div className="grid h-20 w-20 place-items-center border border-dashed border-[var(--border)] text-3xl text-[var(--text-muted)]">
                  +
                </div>
                <div>
                  <strong className="text-[1.35rem]">Логотип бренда</strong>
                  <p className="mt-2 text-[1.1rem] text-[var(--text-secondary)]">
                    PNG или JPG, до 2MB
                  </p>
                </div>
              </div>
            </div>
          </div>
        </article>

        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">
            Каналы продаж
          </h2>
          <p className="mt-4 text-[1.15rem] leading-8 text-[var(--text-secondary)]">
            Выберите платформы, где представлен ваш бренд. Это поможет ИИ адаптировать
            форматы.
          </p>
          <div className="mt-8 grid gap-4">
            {([
              ["Собственный сайт", true],
              ["Wildberries", true],
              ["Ozon", false]
            ] as const).map(([label, selected]) => (
              <div
                className="flex items-center justify-between border border-[var(--border)] bg-[var(--surface)] px-6 py-5 text-[1.2rem]"
                key={label}
              >
                <span>{label}</span>
                <span
                  className={`h-8 w-8 rounded-full border ${
                    selected ? "border-[var(--ai)] bg-[var(--ai)]" : "border-[var(--border)] bg-white"
                  }`}
                />
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="mt-8 grid gap-6">
        <article className="site-card p-8">
          <div className="flex flex-wrap items-start justify-between gap-8">
            <div>
              <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">
                Визуальный стиль бренда
              </h2>
              <p className="mt-4 text-[1.15rem] leading-8 text-[var(--text-secondary)]">
                Цветовая палитра и мудборд, определяющие атмосферу ваших генераций.
              </p>
            </div>
            <button className="site-pill-button" type="button">
              Сгенерировать стиль по описанию
            </button>
          </div>

          <div className="mt-8 grid gap-8 xl:grid-cols-[0.55fr_1fr]">
            <div>
              <p className="text-[1.2rem] font-semibold">Фирменные цвета</p>
              <div className="mt-6 flex gap-4">
                {["#faf7ef", "#dcc49d", "#66666f"].map((color) => (
                  <span
                    className="h-16 w-16 rounded-full border border-[var(--border)]"
                    key={color}
                    style={{ backgroundColor: color }}
                  />
                ))}
                <span className="grid h-16 w-16 place-items-center rounded-full bg-[#e3dfde] text-3xl text-[var(--text-muted)]">
                  +
                </span>
              </div>
            </div>

            <div>
              <p className="text-[1.2rem] font-semibold">Мудборд / Референсы</p>
              <div className="mt-6 grid gap-4 md:grid-cols-3">
                <ImagePlaceholder className="h-[180px]" />
                <ImagePlaceholder className="h-[180px]" />
                <div className="grid h-[180px] place-items-center border border-dashed border-[var(--border)] text-[1.2rem] text-[var(--text-muted)]">
                  Добавить фото
                </div>
              </div>
            </div>
          </div>
        </article>

        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">
            Требования к контенту (ИИ Настройки)
          </h2>
          <div className="mt-8 grid gap-10 xl:grid-cols-[1fr_1fr]">
            <div>
              <p className="text-[1.2rem] font-semibold">Предпочтительный фон для каталога</p>
              <div className="mt-6 flex flex-wrap gap-4">
                {["Студийный светлый", "Городская среда", "Интерьер"].map((item, index) => (
                  <button
                    className="site-pill-button px-8 text-[1.05rem]"
                    data-selected={index === 0 ? "true" : undefined}
                    key={item}
                    type="button"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-[1.2rem] font-semibold">Строгость сохранения деталей кроя</p>
              <div className="mt-8 h-2 rounded-full bg-[#dbd5d1]">
                <div className="h-2 w-[85%] rounded-full bg-[var(--ai)]" />
              </div>
              <div className="mt-4 flex justify-between text-sm text-[var(--text-muted)]">
                <span>Больше креатива</span>
                <span>Точная копия (Выбрано: 85%)</span>
              </div>
            </div>
          </div>
        </article>
      </section>
    </main>
  );
}
