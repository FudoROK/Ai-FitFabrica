import Link from "next/link";
import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";

const statusItems = [
  ["Анализ модели", "Ожидание фото"],
  ["Анализ одежды", "Рубашка • Высокое качество"],
  ["Совмещение пропорций", "Ожидание полных данных"]
] as const;

export default function WorkspaceNewTryOnPage() {
  return (
    <main className="flex h-full min-w-0 flex-col overflow-hidden bg-[var(--background)]">
      <div className="border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 lg:px-6">
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="workspace-title font-[family-name:var(--font-manrope)]">Новая примерка</h1>
            <p className="workspace-subtitle mt-2 max-w-[760px] text-[var(--text-secondary)]">
              Загрузите фото человека и фото одежды для AI-примерки.
            </p>
          </div>

          <Link
            className="site-pill-button site-pill-button--compact"
            href="/workspace/chat"
          >
            Вернуться в общий чат
          </Link>
        </div>
      </div>

      <section className="min-h-0 flex-1 overflow-hidden p-5 lg:p-6">
        <section className="tryon-layout grid h-full min-w-0 gap-5 overflow-hidden">
          <div className="min-h-0 overflow-y-auto overflow-x-hidden">
            <div className="grid gap-5">
              <div className="upload-card flex w-full max-w-[220px] flex-col items-center justify-center border-2 border-dashed border-[#d8c3a5] bg-[var(--surface)] p-6 text-center">
                <div className="h-18 w-18 rounded-full bg-[var(--ai-soft)]" />
                <h2 className="upload-card-title mt-5 font-semibold">Фото человека</h2>
                <p className="upload-card-description mt-2 text-[var(--text-secondary)]">
                  JPEG, PNG до 10MB
                </p>
              </div>

              <div className="upload-card w-full max-w-[220px] border-2 border-dashed border-[#d8c3a5] bg-[var(--surface)] p-4">
                <ImagePlaceholder
                  className="h-[240px] rounded-[1.5rem]"
                  label="Одежда загружена"
                />
              </div>
            </div>
          </div>

          <div className="workspace-main min-h-0 min-w-0 overflow-y-auto overflow-x-hidden">
            <div className="result-card site-card flex min-w-0 items-center justify-center p-8 lg:p-10">
              <div className="text-center">
                <div className="mx-auto h-24 w-24 rounded-full bg-[var(--ai-soft)]" />
                <h2 className="result-title mt-6 font-[family-name:var(--font-manrope)] font-bold tracking-[-0.04em]">
                  Ожидание материалов
                </h2>
                <p className="result-description mx-auto mt-4 max-w-[620px] text-[var(--text-secondary)]">
                  Загрузите фото человека и одежды. AI проанализирует материалы и
                  подготовит примерку.
                </p>
              </div>
            </div>
          </div>

          <aside className="workspace-status min-h-0 overflow-y-auto overflow-x-hidden pr-1">
            <div className="site-card flex min-h-0 flex-col justify-between p-6">
              <div>
                <h2 className="text-[1.35rem] font-semibold">Статус анализа</h2>
                <div className="mt-6 grid gap-4">
                  {statusItems.map(([title, description]) => (
                    <div className="rounded-[1.2rem] bg-[var(--background)] p-4" key={title}>
                      <strong className="block text-[0.95rem]">{title}</strong>
                      <p className="mt-1 text-[0.85rem] leading-6 text-[var(--text-secondary)]">
                        {description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6">
                <div className="mb-4 flex items-center justify-between text-[0.95rem]">
                  <span className="text-[var(--text-secondary)]">Стоимость:</span>
                  <strong>1 кредит</strong>
                </div>
                <SiteButton className="w-full" disabled variant="violet">
                  Сгенерировать примерку
                </SiteButton>
                <p className="mt-3 text-center text-[0.82rem] font-medium text-[var(--text-muted)]">
                  Загрузите все фото для начала
                </p>
              </div>
            </div>
          </aside>
        </section>
      </section>
    </main>
  );
}
