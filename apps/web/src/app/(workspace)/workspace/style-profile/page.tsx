import { SiteButton } from "@/components/site/site-button";

export default function WorkspaceStyleProfilePage() {
  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Style Profile</p>
        <h1 className="workspace-page-title mt-4">Профиль стиля</h1>
        <p className="workspace-page-lead mt-4 max-w-[860px]">
          Здесь живёт личный контекст пользователя: размеры, посадка, любимые сочетания, ограничения по цветам и бюджету. Сохранение профиля не должно
          тратить кредиты и не должно считаться генерацией.
        </p>
      </section>

      <section className="mt-[50px] grid gap-5 xl:grid-cols-3">
        <article className="site-card p-7 lg:p-8">
          <h2 className="workspace-card-title">Размеры и fit</h2>
          <p className="workspace-body mt-4">Эти данные нужны для try-on и stylist explanations, но логика принятия решения остаётся на backend.</p>
        </article>
        <article className="site-card p-7 lg:p-8">
          <h2 className="workspace-card-title">Цвета и предпочтения</h2>
          <p className="workspace-body mt-4">Любимые цвета, избегаемые оттенки, стиль и бюджет помогают делать рекомендации точнее.</p>
        </article>
        <article className="site-card p-7 lg:p-8">
          <h2 className="workspace-card-title">Текущее состояние</h2>
          <p className="workspace-body mt-4">Экран встроен в workspace shell и готов к подключению typed profile DTO без выдуманных AI-результатов.</p>
        </article>
      </section>

      <div className="mt-[50px] flex flex-wrap gap-3">
        <SiteButton href="/workspace/new-fitting" variant="violet">
          Перейти к примерке
        </SiteButton>
        <SiteButton href="/workspace/settings" variant="secondary">
          Вернуться в настройки
        </SiteButton>
      </div>
    </main>
  );
}
