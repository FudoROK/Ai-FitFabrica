import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { MaterialIcon } from "@/components/site/material-icon";
import { SiteButton } from "@/components/site/site-button";

const scenarios = [
  {
    title: "Персональный стилист",
    body: "Примеряйте любую одежду онлайн, находите аналоги дешевле и составляйте идеальные образы с учетом вашей фигуры и цветотипа.",
    bullets: ["Виртуальная примерка", "Поиск дешевых аналогов"]
  },
  {
    title: "Решения для бизнеса",
    body: "Генерация каталогов, виртуальные манекены и автоматизация контента для маркетплейсов. Снижение возвратов за счет точной примерки.",
    bullets: ["Фотосессии без моделей", "Интеграция в магазин"]
  }
];

export default function HomePage() {
  return (
    <main className="pb-20 pt-12 lg:pb-28">
      <section className="site-container">
        <div className="mx-auto max-w-[980px] text-center">
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.6rem,7vw,5.9rem)] font-bold leading-[0.95] tracking-[-0.06em]">
            AI-команда для одежды, покупок и fashion-продаж
          </h1>
          <p className="mx-auto mt-6 max-w-[760px] text-[1.55rem] leading-[1.45] text-[var(--text-secondary)]">
            Виртуальная примерка, создание уникального контента и интеллектуальный анализ стиля в один клик. Переосмыслите свой гардероб или масштабируйте модный бизнес.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <SiteButton href="/for-you">Для себя</SiteButton>
            <SiteButton href="/business" variant="secondary">Для бизнеса</SiteButton>
          </div>
        </div>
        <div className="mt-14">
          <ImagePlaceholder accent="sand" chips={["AI Fitting Active"]} className="h-[420px] w-full" split />
        </div>
      </section>

      <section className="site-container mt-36 grid gap-8 lg:grid-cols-2">
        {scenarios.map((scenario, index) => (
          <article className={`site-card p-10 ${index === 1 ? "bg-[var(--surface-alt)]" : ""}`} key={scenario.title}>
            <MaterialIcon className="mb-6 text-[2rem] text-[var(--ai)]" name={index === 0 ? "person" : "business_center"} />
            <h2 className="font-[family-name:var(--font-manrope)] text-[2.6rem] font-bold tracking-[-0.04em]">{scenario.title}</h2>
            <p className="mt-4 text-[1.1rem] leading-8 text-[var(--text-secondary)]">{scenario.body}</p>
            <div className="mt-8 grid gap-3 text-[1rem] text-[var(--text-secondary)]">
              {scenario.bullets.map((bullet) => (
                <div className="flex items-center gap-3" key={bullet}>
                  <MaterialIcon className="text-[1.1rem] text-[var(--success)]" name="check_circle" />
                  <span>{bullet}</span>
                </div>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="site-container mt-36 text-center">
        <h2 className="font-[family-name:var(--font-manrope)] text-[3.5rem] font-bold tracking-[-0.05em]">
          Готовы изменить свой стиль?
        </h2>
        <p className="mx-auto mt-4 max-w-[640px] text-[1.25rem] leading-8 text-[var(--text-secondary)]">
          Загрузите свое фото и начните виртуальную примерку прямо сейчас.
        </p>
        <SiteButton className="mt-10" href="/workspace/try-on/new" icon="auto_awesome" variant="violet">
          Начать примерку
        </SiteButton>
      </section>
    </main>
  );
}
