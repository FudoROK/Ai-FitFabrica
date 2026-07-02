"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import Image from "next/image";
import { SiteButton } from "@/components/site/site-button";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";
import type { SimilarSearchResponse } from "@/lib/api/contracts";

const acceptedTypes = ["image/jpeg", "image/png", "image/webp"] as const;
const maxFileSize = 10 * 1024 * 1024;

type SelectedGarmentPhoto = {
  error: string;
  file: File | null;
  previewUrl: string;
};

const emptyPhoto: SelectedGarmentPhoto = { error: "", file: null, previewUrl: "" };

function validatePhoto(file: File | null): string {
  if (!file) return "Добавьте фото одежды.";
  if (!acceptedTypes.includes(file.type as (typeof acceptedTypes)[number])) return "Разрешены JPEG, PNG и WebP.";
  if (file.size === 0) return "Файл пустой.";
  if (file.size > maxFileSize) return "Максимальный размер файла - 10 МБ.";
  return "";
}

function formatLocationMatch(value: string): string {
  const labels: Record<string, string> = {
    same_city: "тот же город",
    same_country_delivery: "доставка в ваш город",
    same_country: "та же страна",
    delivery_available: "доставка доступна",
    remote: "удаленный магазин",
    unknown: "локация не указана",
  };
  return labels[value] ?? value;
}

function formatOfferLocation(item: SimilarSearchResponse["results"][number]): string {
  const location = [item.city, item.country_code].filter(Boolean).join(", ");
  const delivery = item.delivery_regions.length > 0 ? `Доставка: ${item.delivery_regions.join(", ")}` : "";
  return [location, delivery].filter(Boolean).join(" · ");
}

function resolveResultImageUrl(imageUrl: string | null): string {
  if (!imageUrl) return "";
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) return imageUrl;
  return `${getApiBaseUrl()}${imageUrl.startsWith("/") ? imageUrl : `/${imageUrl}`}`;
}

function canOpenOffer(offerUrl: string | null): boolean {
  return Boolean(offerUrl && (offerUrl.startsWith("http://") || offerUrl.startsWith("https://")));
}

function buildRedirectUrl(item: SimilarSearchResponse["results"][number]): string {
  const params = new URLSearchParams({
    product_id: item.product_id,
    title: item.title,
    marketplace: item.marketplace,
    offer_url: item.offer_url ?? "",
  });
  if (item.image_url) params.set("image_url", item.image_url);
  if (item.country_code) params.set("user_country_code", item.country_code);
  if (item.city) params.set("user_city", item.city);
  return `${getApiBaseUrl()}/api/similar-search/redirect?${params.toString()}`;
}

export function SimilarSearchWorkflow() {
  const { hasCapability } = useWorkspaceRuntime();
  const [photo, setPhoto] = useState<SelectedGarmentPhoto>(emptyPhoto);
  const [countryCode, setCountryCode] = useState("KZ");
  const [city, setCity] = useState("Almaty");
  const [budgetMax, setBudgetMax] = useState("");
  const [result, setResult] = useState<SimilarSearchResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const canUseSimilarSearch = hasCapability("similar_search_create");
  const hasRequiredData = Boolean(photo.file && !photo.error && countryCode.trim().length === 2 && city.trim());
  const canSubmit = canUseSimilarSearch && hasRequiredData && !isSubmitting;
  const disabledReason = !canUseSimilarSearch
    ? "Поиск похожих товаров недоступен для этого workspace."
    : !hasRequiredData
      ? "Добавьте фото одежды, страну и город."
      : "";

  useEffect(() => () => {
    if (photo.previewUrl) URL.revokeObjectURL(photo.previewUrl);
  }, [photo.previewUrl]);

  function handlePhotoChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    const nextError = validatePhoto(file);
    if (photo.previewUrl) URL.revokeObjectURL(photo.previewUrl);
    setPhoto({
      error: nextError,
      file: nextError ? null : file,
      previewUrl: nextError || !file ? "" : URL.createObjectURL(file),
    });
    setResult(null);
    setError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    if (!canSubmit || !photo.file) return;
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("garment_photo", photo.file);
      formData.append("user_country_code", countryCode.trim().toUpperCase());
      formData.append("user_city", city.trim());
      if (budgetMax.trim()) formData.append("budget_max", budgetMax.trim());
      const client = new WebApiClient(getApiBaseUrl());
      setResult(await client.searchSimilarByGarmentPhoto(formData));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось выполнить поиск.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <form className="site-card p-7 lg:p-8" onSubmit={handleSubmit}>
        <p className="eyebrow">Бесплатный поиск</p>
        <h2 className="workspace-section-title mt-4">Загрузите фото одежды</h2>
        <p className="workspace-body mt-4">
          Backend сам проанализирует вещь через Garment Identity Agent и сначала проверит товары из нашей локальной базы магазинов.
        </p>
        <div className="mt-5 rounded-[24px] border border-[var(--border)] bg-white/70 p-5">
          <p className="text-sm font-semibold text-[var(--text-primary)]">
            Сейчас бесплатно ищем только по одобренной локальной базе магазинов
          </p>
          <div className="mt-3 grid gap-2 text-sm text-[var(--text-muted)]">
            <p>Проверяем только товары, которые прошли админ-проверку и попали в поисковый индекс.</p>
            <p>Покажем сначала ближайшие магазины и доставку в ваш город.</p>
            <p>Внешние маркетплейсы и Instagram подключим отдельным слоем, когда будет готов legal/API contour.</p>
          </div>
        </div>

        <label className="public-form-label mt-6 grid gap-3">
          <span>Фото одежды</span>
          <span className="rounded-[1.5rem] border border-dashed border-[var(--border)] bg-[var(--surface-alt)] p-5">
            <input
              accept="image/jpeg,image/png,image/webp"
              className="sr-only"
              disabled={isSubmitting}
              id="similar-search-garment-photo"
              onChange={handlePhotoChange}
              type="file"
            />
            <span className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span>
                <span className="block text-base font-semibold text-[var(--text-primary)]">
                  {photo.file ? photo.file.name : "Выберите фото товара"}
                </span>
                <span className="workspace-meta mt-1 block">JPEG, PNG или WebP до 10 МБ. Лучше одно фото одной вещи на чистом фоне.</span>
              </span>
              <span className="inline-flex w-fit rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white">
                Загрузить фото
              </span>
            </span>
          </span>
        </label>
        {photo.previewUrl ? (
          <div className="relative mt-4 aspect-[4/3] overflow-hidden rounded-[1.5rem] bg-[var(--surface-alt)]">
            <Image alt="Предпросмотр одежды" fill className="object-contain" src={photo.previewUrl} unoptimized />
          </div>
        ) : null}
        {photo.error ? <p className="workspace-meta mt-3 text-[var(--error)]">{photo.error}</p> : null}

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <label className="public-form-label grid gap-3">
            <span>Страна</span>
            <input
              className="site-input"
              disabled={isSubmitting}
              maxLength={2}
              onChange={(event) => setCountryCode(event.target.value.toUpperCase())}
              value={countryCode}
            />
          </label>
          <label className="public-form-label grid gap-3">
            <span>Город</span>
            <input className="site-input" disabled={isSubmitting} onChange={(event) => setCity(event.target.value)} value={city} />
          </label>
        </div>

        <label className="public-form-label mt-4 grid gap-3">
          <span>Бюджет, необязательно</span>
          <input
            className="site-input"
            disabled={isSubmitting}
            inputMode="decimal"
            onChange={(event) => setBudgetMax(event.target.value)}
            placeholder="Например 20000"
            value={budgetMax}
          />
        </label>

        {error ? <p className="mt-5 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
        <SiteButton className="mt-7 w-full" disabled={!canSubmit} type="submit" variant="violet">
          {isSubmitting ? "Ищем похожие товары..." : "Найти похожее бесплатно"}
        </SiteButton>
        {disabledReason ? <p className="workspace-meta mt-3">{disabledReason}</p> : null}
        <p className="workspace-meta mt-4">
          Базовый поиск бесплатный. Платные действия подключаются отдельно: примерка, глубокий внешний поиск и расширенная аналитика.
        </p>
      </form>

      <section className="site-card p-7 lg:p-8">
        <p className="eyebrow">Результаты</p>
        <h2 className="workspace-section-title mt-4">Похожие товары из локальной базы</h2>
        {!result && !isSubmitting ? (
          <p className="workspace-body mt-4">После поиска здесь появятся реальные товары магазинов или честное пустое состояние.</p>
        ) : null}
        {isSubmitting ? <p className="workspace-body mt-4">Анализируем одежду и проверяем локальный каталог...</p> : null}
        {result && result.results.length === 0 ? (
          <div className="mt-6 rounded-[1.5rem] border border-dashed border-[var(--border)] p-6">
            <h3 className="workspace-card-title">Пока ничего не найдено</h3>
            <p className="workspace-body mt-3">
              Это не ошибка. Значит в локальном каталоге пока нет достаточно похожих утвержденных товаров.
            </p>
            <p className="workspace-body mt-3">
              Если ничего не найдено, это не ошибка оплаты и не списание credits. Можно попробовать другое фото, другой город или дождаться расширения каталога.
            </p>
          </div>
        ) : null}
        {result && result.results.length > 0 ? (
          <div className="mt-6 grid gap-4">
            {result.results.map((item) => (
              <article className="rounded-[1.5rem] border border-[var(--border)] bg-white p-5" key={`${item.product_id}-${item.marketplace}`}>
                <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
                  <div className="flex aspect-square items-center justify-center overflow-hidden rounded-[1.25rem] bg-[var(--surface-alt)]">
                    {resolveResultImageUrl(item.image_url) ? (
                      <Image
                        alt={item.title}
                        className="h-full w-full object-contain"
                        height={120}
                        src={resolveResultImageUrl(item.image_url)}
                        unoptimized
                        width={120}
                      />
                    ) : (
                      <span className="px-3 text-center text-xs font-semibold text-[var(--text-muted)]">Фото товара</span>
                    )}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="workspace-card-title">{item.title}</h3>
                        <p className="workspace-meta mt-2">{formatLocationMatch(item.location_match)} · {item.marketplace}</p>
                        {formatOfferLocation(item) ? <p className="workspace-meta mt-1">{formatOfferLocation(item)}</p> : null}
                      </div>
                      <p className="rounded-full bg-[var(--surface-alt)] px-4 py-2 text-sm font-semibold text-[var(--text-primary)]">
                        {item.price_amount.toLocaleString("ru-RU")} {item.currency}
                      </p>
                    </div>
                    <p className="workspace-body mt-4">{item.explanation}</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <span className="rounded-full bg-[#eee8ff] px-3 py-1 text-xs font-semibold text-[#34227d]">
                        Сходство {Math.round(item.similarity_score * 100)}%
                      </span>
                      {item.is_cheaper_alternative ? (
                        <span className="rounded-full bg-[#f3eadf] px-3 py-1 text-xs font-semibold text-[var(--text-primary)]">
                          дешевле референса
                        </span>
                      ) : null}
                    </div>
                    <div className="mt-5">
                      {canOpenOffer(item.offer_url) ? (
                        <a
                          className="site-pill-button inline-flex"
                          href={buildRedirectUrl(item)}
                          rel="noopener noreferrer"
                          target="_blank"
                        >
                          Посмотреть товар
                        </a>
                      ) : (
                        <button className="site-pill-button inline-flex opacity-50" disabled type="button">
                          Товар в локальном каталоге
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}
