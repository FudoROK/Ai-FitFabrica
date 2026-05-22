import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

export default function ForYouPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.7rem,7vw,5.8rem)] font-bold leading-[0.94] tracking-[-0.06em]">
            Одежда, которая подходит именно вам
          </h1>
          <p className="mt-6 max-w-[520px] text-[1.35rem] leading-8 text-[var(--text-secondary)]">
            Загрузите своё фото и виртуально примеряйте одежду любых брендов. Наш ИИ учитывает ваши пропорции, анализирует фасон и предлагает лучшие варианты.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <SiteButton href="/workspace/try-on/new" icon="auto_awesome" variant="violet">Начать примерку</SiteButton>
            <SiteButton href="/workspace/similar" icon="search" variant="secondary">Найти похожее дешевле</SiteButton>
          </div>
        </div>
        <ImagePlaceholder accent="sand" chips={["Идеальная посадка", "Пропорции учтены"]} className="h-[570px]" split />
      </section>

      <section className="site-container mt-32">
        <div className="text-center">
          <h2 className="font-[family-name:var(--font-manrope)] text-[3.3rem] font-bold tracking-[-0.05em]">Виртуальная примерочная</h2>
          <p className="mt-4 text-[1.2rem] text-[var(--text-secondary)]">От фотографии до готового образа за несколько секунд.</p>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          <article className="site-card p-8"><h3 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold tracking-[-0.04em]">Загрузите фото</h3><p className="mt-4 text-[var(--text-secondary)]">Сделайте снимок в полный рост при хорошем освещении.</p><div className="mt-8 rounded-[1.75rem] border-2 border-dashed border-[#d8c3a5] bg-white p-16 text-center text-[var(--text-muted)]">Выбрать файл</div></article>
          <article className="site-card p-8"><h3 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold tracking-[-0.04em]">Выберите одежду</h3><p className="mt-4 text-[var(--text-secondary)]">Укажите ссылку на товар или загрузите скриншот.</p><div className="mt-8 grid gap-4"><div className="rounded-[1.25rem] border border-[var(--border)] bg-white p-4">Шелковая блуза</div><div className="rounded-[1.25rem] border border-[var(--border)] bg-white p-4">Брюки палаццо</div></div></article>
          <article className="site-card p-8"><h3 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold tracking-[-0.04em]">Оцените результат</h3><p className="mt-4 text-[var(--text-secondary)]">ИИ аккуратно &quot;наденет&quot; вещь, сохранив текстуру и тени.</p><ImagePlaceholder className="mt-8 h-[280px]" /></article>
        </div>
      </section>

      <section className="site-container mt-24">
        <div className="rounded-[2.5rem] bg-[var(--surface-alt)] p-9">
          <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">Глубокий анализ стиля</h2>
          <p className="mt-4 max-w-[780px] text-[1.15rem] leading-8 text-[var(--text-secondary)]">Нейросеть оценивает не только размер, но и то, как вещь взаимодействует с вашим типом фигуры и колоритом.</p>
          <div className="mt-10 grid gap-6 lg:grid-cols-[1.5fr_0.9fr]"><div className="site-card p-8"><h3 className="text-[1.8rem] font-semibold">Анализ палитры</h3><div className="mt-8 flex gap-3">{["#d9c099", "#9c9898", "#2d2b2f", "#8d79f0"].map((color) => <span className="h-10 flex-1 rounded-none" key={color} style={{ backgroundColor: color }} />)}</div></div><div className="site-card p-8"><h3 className="text-[1.8rem] font-semibold">Пропорции</h3><ul className="mt-6 grid gap-4 text-[var(--text-secondary)]"><li>Длина макси</li><li>Высокая посадка</li><li className="text-[var(--warning)]">Осторожно с oversize</li></ul></div></div>
          <div className="mt-6 rounded-[2rem] border border-[#c6b8ff] bg-[#ece6ff] px-8 py-7"><p className="text-sm uppercase tracking-[0.16em] text-[var(--ai)]">AI стилист</p><h3 className="mt-3 font-[family-name:var(--font-manrope)] text-[2rem] font-bold tracking-[-0.04em]">Персональные рекомендации</h3><p className="mt-3 max-w-[820px] text-[var(--text-secondary)]">На основе ваших сохраненных образов и анализа внешности, мы подобрали 15 капсульных вещей, которые идеально дополнят ваш гардероб на этот сезон.</p></div>
        </div>
      </section>
    </main>
  );
}
