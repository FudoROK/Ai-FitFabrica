import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceProductCardPage() {
  return (
    <main className="grid min-h-screen xl:grid-cols-[1fr_1.1fr_0.8fr]">
      <section className="border-r border-[var(--border)] px-8 py-8">
        <h1 className="font-[family-name:var(--font-manrope)] text-[4.5rem] font-bold tracking-[-0.06em]">
          Новая карточка
        </h1>
        <p className="mt-2 text-[1.25rem] text-[var(--text-secondary)]">
          Настройка параметров товара
        </p>

        <div className="mt-10 grid gap-8">
          <div>
            <h2 className="mb-4 text-[1.8rem] font-semibold">Фото товара</h2>
            <div className="rounded-[2.2rem] border-2 border-dashed border-[#d8c3a5] p-10 text-center text-[1.2rem] text-[var(--text-secondary)]">
              Загрузить фото
              <br />
              Перетащите файл или нажмите для выбора. PNG, JPG до 10MB.
            </div>
          </div>

          <label className="grid gap-3 text-[1.2rem] font-semibold">
            <span>Название</span>
            <input className="site-input" placeholder="Например: Шелковое платье миди" />
          </label>

          <label className="grid gap-3 text-[1.2rem] font-semibold">
            <span>Категория</span>
            <select className="site-select appearance-none">
              <option>Платья</option>
              <option>Пальто</option>
              <option>Костюмы</option>
            </select>
          </label>

          <div>
            <p className="mb-4 text-[1.2rem] font-semibold">Площадка</p>
            <div className="grid grid-cols-2 gap-3">
              <button className="site-pill-button w-full" data-selected="true" type="button">
                Instagram
              </button>
              <button className="site-pill-button w-full" type="button">
                Маркетплейс
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="flex flex-col border-r border-[var(--border)] bg-[#f3f0ef] px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">
            Предпросмотр вариантов
          </h2>
          <div className="flex gap-3">
            <span className="rounded-full bg-white px-4 py-4">◫</span>
            <span className="rounded-full bg-white px-4 py-4">▣</span>
          </div>
        </div>

        <div className="site-card p-6">
          <ImagePlaceholder chips={["AI ожидает фото"]} className="h-[430px]" />
          <div className="mt-6 grid grid-cols-4 gap-4">
            <div className="h-16 bg-[#e4dfdd]" />
            <div className="h-16 bg-[#e4dfdd]" />
            <div className="h-16 bg-[#e4dfdd]" />
            <div className="grid h-16 place-items-center bg-[#e4dfdd] text-3xl">+</div>
          </div>
        </div>

        <SiteButton className="mt-auto w-full" href="/workspace/content-package" icon="auto_awesome">
          Создать контент-пакет
        </SiteButton>
      </section>

      <aside className="flex flex-col bg-[#f3efff] px-8 py-8">
        <h2 className="font-[family-name:var(--font-manrope)] text-[2.8rem] font-bold tracking-[-0.04em]">
          AI Анализ
        </h2>
        <p className="mt-3 text-[1.1rem] text-[var(--text-secondary)]">
          Оценка качества исходника
        </p>

        <div className="mt-10 border border-[var(--border)] bg-white p-5 text-[1.15rem]">
          <strong>Ожидание фото</strong>
          <p className="mt-2 text-[var(--text-secondary)]">Загрузите товар для анализа</p>
        </div>

        <div className="mt-10 grid gap-5 text-[1.1rem] text-[var(--text-secondary)]">
          <strong className="text-black">Рекомендации</strong>
          <span>Фон: Однородный и светлый</span>
          <span>Освещение: Без резких теней</span>
          <span>Ракурс: Товар по центру кадра</span>
        </div>

        <div className="mt-auto rounded-[2rem] border border-[#cdbfff] bg-white p-6 text-[1.1rem] leading-8 text-[var(--ai)]">
          При создании пакета нейросеть автоматически улучшит резкость и цветопередачу
          исходного фото.
        </div>
      </aside>
    </main>
  );
}
