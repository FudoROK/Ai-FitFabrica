"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";
import type { BusinessCatalogImportResponse } from "@/lib/api/business-catalog-contracts";

export function BusinessCatalogImportPage() {
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [result, setResult] = useState<BusinessCatalogImportResponse | null>(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = csvFile !== null && !isSubmitting;

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setError("");
    setResult(null);
    const nextFile = event.target.files?.[0] ?? null;
    if (nextFile === null) {
      setCsvFile(null);
      return;
    }
    if (!nextFile.name.toLowerCase().endsWith(".csv")) {
      setCsvFile(null);
      setError("Сейчас поддерживается только CSV-файл.");
      return;
    }
    setCsvFile(nextFile);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!canSubmit || csvFile === null) {
      setError("Выберите CSV-файл для импорта.");
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = new FormData();
      payload.append("file", csvFile);
      const client = new WebApiClient(getApiBaseUrl());
      setResult(await client.createBusinessCatalogImport(payload));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить CSV-файл.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Импорт каталога</p>
        <h1 className="workspace-page-title mt-4">CSV-файл с товарами</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Загрузите CSV с колонками title, category, price_amount, currency, country_code, city, availability,
          product_url, delivery_regions. Backend примет корректные строки и вернёт ошибки по плохим строкам.
        </p>
      </section>

      <form className="mt-[50px] grid gap-5 xl:grid-cols-[0.9fr_1.1fr]" onSubmit={handleSubmit}>
        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Загрузка каталога</h2>
          <label className="public-form-label mt-6 grid gap-3">
            <span>CSV-файл</span>
            <input accept=".csv,text/csv" disabled={isSubmitting} onChange={handleFileChange} type="file" />
          </label>
          <div className="mt-5 rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
            <p className="text-sm font-semibold text-[var(--text-primary)]">CSV limits</p>
            <p className="workspace-body mt-2">
              Коротко: standard: 1,000 rows / 5 MB. large: 25,000 rows / 50 MB.
            </p>
            <details className="mt-3">
              <summary className="cursor-pointer text-sm font-semibold text-[var(--text-primary)]">
                Detailed upload limits
              </summary>
              <ul className="mt-3 grid gap-2 text-sm text-[var(--text-muted)]">
                <li>Формат: только CSV в кодировке UTF-8.</li>
                <li>Обязательные колонки: title, category, price_amount, currency, country_code, city, availability, product_url, delivery_regions.</li>
                <li>Если файл больше лимита, backend вернёт business_catalog_backpressure без частичного импорта.</li>
                <li>large-tier назначает администратор после проверки нагрузки магазина.</li>
              </ul>
            </details>
          </div>
          {csvFile ? <p className="workspace-body mt-4">Выбран файл: {csvFile.name}</p> : null}
          {error ? <p className="mt-6 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
          <div className="mt-8 flex flex-wrap gap-3">
            <SiteButton disabled={!canSubmit} type="submit">
              {isSubmitting ? "Загружаем CSV" : "Импортировать CSV"}
            </SiteButton>
            <SiteButton href="/workspace/business-catalog" variant="secondary">
              Вернуться в каталог
            </SiteButton>
          </div>
        </section>

        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Результат импорта</h2>
          {result ? (
            <div className="mt-6 grid gap-4">
              <p className="workspace-card-title">Импорт завершён: {result.import_job.status}</p>
              <p className="workspace-body">
                Принято строк: {result.import_job.accepted_rows}. Ошибок: {result.import_job.rejected_rows}.
              </p>
              {result.errors.length > 0 ? (
                <div className="grid gap-3">
                  {result.errors.map((item) => (
                    <article className="rounded-[1.5rem] border border-[var(--border)] p-4" key={`${item.row_number}-${item.safe_code}-${item.field_name}`}>
                      <p className="workspace-body font-semibold">
                        Строка {item.row_number}: {item.safe_code}
                      </p>
                      <p className="workspace-body mt-2">{item.message}</p>
                    </article>
                  ))}
                </div>
              ) : null}
            </div>
          ) : (
            <p className="workspace-body mt-4">После загрузки здесь появится статус import job и ошибки строк.</p>
          )}
        </section>
      </form>
    </main>
  );
}
