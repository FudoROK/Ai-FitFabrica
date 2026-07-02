import { ContactForm } from "@/features/public/contact-form";
import { SiteButton } from "@/components/site/site-button";

export default function ContactsPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container grid gap-10 lg:grid-cols-[0.95fr_1fr]">
        <div>
          <p className="eyebrow text-[var(--ai)]">Контакты</p>
          <h1 className="hero-title mt-5">Свяжитесь с командой FitFabrica</h1>
          <p className="hero-lead mt-6 max-w-[720px]">
            Если вы хотите подключить FitFabrica для бренда, каталога или контент-команды,
            оставьте заявку. Мы разберем текущий процесс, покажем рабочий контур и предложим
            реалистичный сценарий внедрения.
          </p>

          <div className="site-card mt-10 p-10">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">Быстрый старт</p>
            <h2 className="workspace-card-title mt-5">Хотите попробовать продукт прямо сейчас?</h2>
            <p className="public-body mt-5 max-w-[560px]">
              Оцените пользовательский сценарий на реальном workflow: загрузите фото и откройте
              новый try-on поток без ожидания демонстрации.
            </p>
            <SiteButton className="mt-8" href="/workspace/new-fitting">
              Начать примерку
            </SiteButton>
          </div>

          <div className="public-body mt-14 grid gap-7">
            <div>
              <strong className="block text-black">Email</strong>
              <span className="text-[var(--text-secondary)]">hello@fitfabrica.ai</span>
            </div>
            <div>
              <strong className="block text-black">Фокус</strong>
              <span className="text-[var(--text-secondary)]">Fashion-tech workflows, контент и product operations</span>
            </div>
          </div>
        </div>

        <ContactForm />
      </section>
    </main>
  );
}
