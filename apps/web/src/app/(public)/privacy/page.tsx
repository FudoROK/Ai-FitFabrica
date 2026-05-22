import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { MaterialIcon } from "@/components/site/material-icon";

export default function PrivacyPage() {
  return (
    <main className="bg-[#fcfbf8] pb-20 pt-12">
      <section className="site-container text-center">
        <div className="mx-auto inline-flex items-center gap-3 rounded-full bg-[#eee7e4] px-6 py-4 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--text-secondary)]">
          <MaterialIcon name="lock" />
          <span>Доверие и контроль</span>
        </div>
        <h1 className="mx-auto mt-8 max-w-[900px] font-[family-name:var(--font-manrope)] text-[clamp(3.6rem,7vw,5.8rem)] font-bold leading-[0.94] tracking-[-0.06em]">Приватность и безопасность</h1>
        <p className="mx-auto mt-6 max-w-[860px] text-[1.35rem] leading-8 text-[var(--text-secondary)]">Ваши данные принадлежат только вам. Мы создали инфраструктуру AI FitFabrica с фундаментальным упором на защиту личной информации, используя передовые стандарты шифрования.</p>
      </section>
      <section className="site-container mt-20 grid gap-6 lg:grid-cols-[1.7fr_0.8fr]">
        <article className="site-card p-9"><p className="inline-flex rounded-full bg-[var(--success-soft)] px-5 py-2 text-sm font-semibold text-[var(--success)]">Строго конфиденциально</p><h2 className="mt-8 font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">Использование фото</h2><p className="mt-4 text-[1.12rem] leading-8 text-[var(--text-secondary)]">Загруженные вами фотографии используются исключительно алгоритмами машинного обучения для генерации примерки одежды в реальном времени. Мы не используем ваши изображения для обучения публичных моделей, не передаем их третьим лицам и не публикуем без вашего прямого согласия.</p></article>
        <article className="site-card bg-[var(--surface-alt)] p-9"><h2 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.05em]">Хранение данных</h2><p className="mt-4 text-[1.12rem] leading-8 text-[var(--text-secondary)]">Вся чувствительная информация хранится на защищенных серверах с использованием стандарта AES-256. Исходные фотографии автоматически удаляются через 30 дней неактивности.</p></article>
      </section>
      <section className="site-container mt-10">
        <div className="overflow-hidden rounded-[2.75rem] bg-[#111015] px-8 py-10 text-white lg:grid lg:grid-cols-[0.9fr_1fr] lg:gap-12">
          <div><h2 className="font-[family-name:var(--font-manrope)] text-[3.2rem] font-bold leading-[0.98] tracking-[-0.05em]">Безопасность уровня enterprise</h2><p className="mt-6 text-[1.15rem] leading-8 text-white/75">Мы регулярно проходим независимые аудиты безопасности. Наши системы спроектированы так, чтобы противостоять современным киберугрозам, обеспечивая непрерывную защиту вашего профиля и сгенерированного контента.</p></div>
          <ImagePlaceholder accent="dark" className="mt-10 h-[320px] lg:mt-0" />
        </div>
      </section>
    </main>
  );
}
