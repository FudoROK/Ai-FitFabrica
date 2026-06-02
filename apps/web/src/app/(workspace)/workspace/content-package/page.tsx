import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceContentPackagePage() {
  return (
    <main className="px-8 py-8 lg:px-12">
      <div className="flex flex-wrap items-start justify-between gap-6 border-b border-[var(--border)] pb-8">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[4rem] font-bold leading-[0.96] tracking-[-0.06em]">
            Готовый контент-пакет
          </h1>
          <p className="mt-3 text-[1.15rem] text-[var(--text-secondary)]">
            Готово • Сгенерировано 12 окт 2023
          </p>
        </div>
        <div className="flex flex-wrap gap-4">
          <SiteButton href="/workspace/history" variant="secondary">
            Сохранить
          </SiteButton>
          <SiteButton href="/workspace/product-card" variant="secondary">
            Экспортировать
          </SiteButton>
          <SiteButton disabled variant="primary">
            Скачать все (ZIP)
          </SiteButton>
        </div>
      </div>

      <p className="mt-4 text-sm text-[var(--text-secondary)]">
        ZIP-экспорт пока показывается как disabled state: backend-экспорт для архива
        будет подключен отдельным workflow.
      </p>

      <section className="mt-10">
        <h2 className="font-[family-name:var(--font-manrope)] text-[3.4rem] font-bold tracking-[-0.05em]">
          Визуальные материалы
        </h2>
        <div className="mt-8 grid gap-6 xl:grid-cols-[1.1fr_0.5fr]">
          <article className="site-card p-6">
            <p className="mb-4 text-sm font-semibold">Главное фото (White Background)</p>
            <ImagePlaceholder className="h-[520px]" />
          </article>
          <div className="grid gap-6">
            <article className="site-card p-4">
              <p className="mb-4 text-sm font-semibold">Карточка маркетплейса</p>
              <ImagePlaceholder className="h-[230px]" />
              <div className="mt-4 rounded-[1.75rem] border border-[var(--border)] p-6 text-center text-[1.1rem] text-[var(--text-secondary)]">
                Оптимизировано для Ozon/WB
                <br />
                Пропорции 3:4, контрастный текст, инфографика преимуществ.
              </div>
            </article>
          </div>
        </div>
        <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.5fr]">
          <article className="site-card p-6">
            <p className="mb-4 text-sm font-semibold">Фото на модели (AI Сгенерировано)</p>
            <ImagePlaceholder className="h-[460px]" chips={["AI Model"]} />
          </article>
          <article className="site-card p-5">
            <p className="mb-4 text-sm font-semibold">Пост Instagram</p>
            <ImagePlaceholder className="h-[240px]" />
            <div className="mt-4 rounded-[1.75rem] border border-[var(--border)] p-5 text-[1rem] leading-7 text-[var(--text-secondary)]">
              Встречайте идеальный тренч для этого сезона. Лаконичный крой,
              премиальная ткань и уверенная посадка для городского образа.
            </div>
          </article>
        </div>
      </section>

      <section className="mt-10 grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[2.6rem] font-bold tracking-[-0.04em]">
            SEO Описание товара
          </h2>
          <p className="mt-6 text-[1.1rem] leading-8 text-[var(--text-secondary)]">
            Название: Тренчкот женский базовый длинный двубортный, бежевый премиум.
            Классический двубортный тренчкот — незаменимая инвестиция в базовый
            гардероб. Выполнен из плотного габардина с водоотталкивающей пропиткой.
          </p>
          <div className="mt-6 rounded-[1.5rem] bg-[var(--surface-alt)] p-4 text-[0.95rem] text-[var(--text-muted)]">
            Ключевые слова: тренч женский, плащ демисезонный, базовый гардероб,
            пальто легкое.
          </div>
          <SiteButton className="mt-6 w-full" variant="secondary">
            Копировать текст
          </SiteButton>
        </article>

        <article className="site-card p-8">
          <h2 className="font-[family-name:var(--font-manrope)] text-[2.6rem] font-bold tracking-[-0.04em]">
            Рекомендации по цене
          </h2>
          <p className="mt-6 text-[1.15rem] text-[var(--text-secondary)]">
            Рекомендуемая розничная цена
          </p>
          <div className="mt-2 flex items-end justify-between">
            <strong className="text-[3.8rem] font-semibold">12 490 ₽</strong>
            <span className="rounded-full bg-[var(--success-soft)] px-4 py-3 text-sm font-semibold text-[var(--success)]">
              Высокий спрос
            </span>
          </div>
          <div className="mt-6 h-2 rounded-full bg-[#e1dbd7]">
            <div className="h-2 w-2/5 rounded-full bg-black" />
          </div>
          <div className="mt-6 rounded-[1.75rem] border border-[var(--border)] p-5 text-[1rem] leading-7 text-[var(--text-secondary)]">
            Визуальное качество контента позволяет позиционировать товар в сегменте
            "Premium Basic". Рекомендуем установить базовую цену 14 990 ₽ с
            постоянной скидкой до 12 490 ₽.
          </div>
        </article>
      </section>
    </main>
  );
}
