const steps = [
  [
    "Шаг 1",
    "Выбор сценария",
    "Пользователь или команда выбирают задачу: примерка, подбор образа, карточка товара или контент-пакет."
  ],
  [
    "Шаг 2",
    "Подготовка входных данных",
    "Система принимает только нужные материалы: фото, товарный референс, профиль бренда или параметры workflow."
  ],
  [
    "Шаг 3",
    "Backend orchestration",
    "Backend валидирует вход, выбирает нужный поток и готовит вызовы AI- и сервисных слоев."
  ],
  [
    "Шаг 4",
    "Проверка качества",
    "До выдачи результата платформа оценивает состояние артефакта и определяет, нужен ли repair, retry или следующий шаг."
  ],
  [
    "Шаг 5",
    "Рабочий результат",
    "Пользователь получает не просто картинку, а структурированный outcome со статусом, заметками и действиями продолжения."
  ],
  [
    "Шаг 6",
    "Продолжение workflow",
    "Результат можно сохранить, отправить в history, использовать для outfit builder или для product-content потока."
  ]
] as const;

export default function HowItWorksPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container text-center">
        <p className="eyebrow">Как это работает</p>
        <h1 className="hero-title mx-auto mt-5 max-w-[820px]">Прозрачный поток от входных данных до результата</h1>
        <p className="hero-lead mx-auto mt-6 max-w-[860px]">
          FitFabrica не строится вокруг случайных AI-демо. Каждый сценарий ведет пользователя через
          короткие, понятные этапы с backend-управлением, проверками и следующими действиями.
        </p>
      </section>

      <section className="site-container mt-20 grid gap-6 lg:grid-cols-3">
        {steps.map(([step, title, body], index) => (
          <article className={`site-card p-8 ${index === 2 || index === 3 ? "bg-[#ebe6ff]" : ""}`} key={title}>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">{step}</p>
            <h2 className="mt-5 workspace-card-title">{title}</h2>
            <p className="public-body mt-5">{body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
