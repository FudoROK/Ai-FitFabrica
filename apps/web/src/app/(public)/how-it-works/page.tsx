const steps = [
  ["Шаг 1", "Выбор задачи", "Определите цель: виртуальная примерка, создание лукбука, подбор похожих вещей или генерация карточек для маркетплейса."],
  ["Шаг 2", "Загрузка", "Предоставьте исходные данные: фотографии одежды, референсы моделей или текстовое описание желаемого результата."],
  ["Шаг 3", "AI Анализ", "Нейросеть анализирует текстуру ткани, посадку, освещение и особенности фигуры для подготовки безупречной генерации."],
  ["Шаг 4", "Генерация", "Создание фотореалистичных изображений. AI применяет сложные алгоритмы диффузии для сохранения детализации."],
  ["Шаг 5", "Проверка качества", "Автоматический контроль результатов: проверка теней, анатомической корректности и соответствия исходному ТЗ."],
  ["Шаг 6", "Результат", "Готовые изображения высокого разрешения, доступные для скачивания, экспорта на маркетплейсы или дальнейшего редактирования."]
];

export default function HowItWorksPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container text-center">
        <h1 className="mx-auto max-w-[820px] font-[family-name:var(--font-manrope)] text-[clamp(3.5rem,7vw,5.7rem)] font-bold leading-[0.95] tracking-[-0.06em]">Искусство автоматизации</h1>
        <p className="mx-auto mt-6 max-w-[860px] text-[1.35rem] leading-8 text-[var(--text-secondary)]">От идеи до готового образа. Мы объединили передовые AI-алгоритмы с безупречным чувством стиля, чтобы сделать процесс создания модного контента прозрачным и предсказуемым.</p>
      </section>
      <section className="site-container mt-20 grid gap-6 lg:grid-cols-3">
        {steps.map(([step, title, body], index) => (
          <article className={`site-card p-8 ${index === 2 || index === 3 ? "bg-[#ebe6ff]" : ""}`} key={title}>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">{step}</p>
            <h2 className="mt-5 font-[family-name:var(--font-manrope)] text-[2.1rem] font-bold tracking-[-0.04em]">{title}</h2>
            <p className="mt-5 text-[1.05rem] leading-8 text-[var(--text-secondary)]">{body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
