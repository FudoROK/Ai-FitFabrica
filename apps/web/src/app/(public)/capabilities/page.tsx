const groups = [
  {
    title: "Для себя",
    items: [
      ["Умная примерка", "Примеряйте одежду на свои фотографии с невероятной точностью."],
      ["Анализ гардероба", "Загрузите фотографии своих вещей, и искусственный интеллект предложит новые сочетания."],
      ["AI Стилист", "Получите персональные рекомендации по стилю, цветовой палитре и крою одежды."],
      ["Поиск аналогов", "Загрузите фото понравившейся вещи, и мы найдем похожие модели дешевле."]
    ]
  },
  {
    title: "Для бизнеса",
    items: [
      ["Генерация карточек", "Автоматическое создание продающих описаний, заголовков и SEO-тегов."],
      ["Фото на модели", "Генерируйте студийные фотографии вашей одежды на виртуальных моделях."],
      ["Контент-пакет", "Создавайте готовые образы для социальных сетей и маркетплейсов."],
      ["Аналитика цен", "Получайте ИИ-рекомендации по оптимальному ценообразованию."]
    ]
  }
];

export default function CapabilitiesPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container text-center">
        <h1 className="mx-auto max-w-[700px] font-[family-name:var(--font-manrope)] text-[clamp(3.4rem,7vw,5.6rem)] font-bold leading-[0.95] tracking-[-0.06em]">Инструменты будущего</h1>
        <p className="mx-auto mt-6 max-w-[760px] text-[1.35rem] leading-8 text-[var(--text-secondary)]">Откройте для себя интеллектуальные решения на базе ИИ. Независимо от того, обновляете ли вы личный гардероб или масштабируете модный бизнес, наши алгоритмы обеспечат идеальный результат.</p>
      </section>
      <section className="site-container mt-24 grid gap-16">
        {groups.map((group) => (
          <div key={group.title}>
            <h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">{group.title}</h2>
            <div className="mt-8 grid gap-6 lg:grid-cols-2">
              {group.items.map(([title, body], index) => (
                <article className={`site-card p-8 ${index % 2 === 1 ? "bg-[var(--surface-alt)]" : ""}`} key={title}>
                  <h3 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold tracking-[-0.04em]">{title}</h3>
                  <p className="mt-4 text-[1.05rem] leading-8 text-[var(--text-secondary)]">{body}</p>
                  <p className="mt-8 text-sm font-semibold">{index < 2 ? "Попробовать →" : "Узнать больше →"}</p>
                </article>
              ))}
            </div>
          </div>
        ))}
      </section>
    </main>
  );
}
