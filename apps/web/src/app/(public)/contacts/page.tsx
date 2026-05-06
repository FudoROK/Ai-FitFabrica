import { VisualPlaceholder } from "@/components/ui/visual-placeholder";
import { ContactForm } from "@/features/public/contact-form";

export default function ContactsPage() {
  return (
    <main className="public-page">
      <section className="page-shell hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Контакты</p>
          <h1 className="hero-title">Подключите FitFabrica под ваш реальный процесс</h1>
          <p className="hero-lead">
            Эта страница теперь не имитирует форму через картинку. Здесь живет рабочая форма
            запроса демо и отдельный placeholder для будущего product visual.
          </p>
        </div>
        <VisualPlaceholder
          data={{
            eyebrow: "Contact Placeholder",
            title: "Место для enterprise visual",
            body: "Позже сюда можно вставить иллюстрацию команды, workflow map или пример brand dashboard.",
            items: ["Brand flow", "Demo scope", "Channels", "Integration plan"]
          }}
        />
      </section>
      <section className="page-shell section-shell">
        <ContactForm />
      </section>
    </main>
  );
}
