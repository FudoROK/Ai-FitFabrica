import { ContactForm } from "@/features/public/contact-form";
import { SiteButton } from "@/components/site/site-button";

export default function ContactsPage() {
  return (
    <main className="pb-20 pt-12">
      <section className="site-container grid gap-10 lg:grid-cols-[0.95fr_1fr]">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(3.6rem,7vw,5.7rem)] font-bold leading-[0.95] tracking-[-0.06em]">Свяжитесь с нами</h1>
          <p className="mt-6 max-w-[720px] text-[1.35rem] leading-[1.6] text-[var(--text-secondary)]">Узнайте, как AI FitFabrica может трансформировать ваш fashion-бизнес. Заполните форму, и наша команда свяжется с вами для проведения персональной демонстрации.</p>
          <div className="site-card mt-10 p-10">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--ai)]">Мгновенный старт</p>
            <h2 className="mt-5 font-[family-name:var(--font-manrope)] text-[3rem] font-bold leading-[0.96] tracking-[-0.05em]">Готовы попробовать прямо сейчас?</h2>
            <p className="mt-5 max-w-[560px] text-[1.15rem] leading-8 text-[var(--text-secondary)]">Оцените качество нашей нейросети, загрузив свое фото в разделе быстрой примерки.</p>
            <SiteButton className="mt-8" href="/workspace/new-fitting">Начать примерку</SiteButton>
          </div>
          <div className="mt-14 grid gap-7 text-[1.12rem]">
            <div><strong className="block text-black">Email</strong><span className="text-[var(--text-secondary)]">hello@fitfabrica.ai</span></div>
            <div><strong className="block text-black">Офис</strong><span className="text-[var(--text-secondary)]">Инновационный центр, Москва</span></div>
          </div>
        </div>
        <ContactForm />
      </section>
    </main>
  );
}
