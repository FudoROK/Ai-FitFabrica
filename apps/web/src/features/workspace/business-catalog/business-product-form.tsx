"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";
import type { BusinessProductAvailability } from "@/lib/api/business-catalog-contracts";

const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;

export function BusinessProductForm() {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [priceAmount, setPriceAmount] = useState("");
  const [currency, setCurrency] = useState("KZT");
  const [countryCode, setCountryCode] = useState("KZ");
  const [city, setCity] = useState("");
  const [availability, setAvailability] = useState<BusinessProductAvailability>("in_stock");
  const [deliveryRegions, setDeliveryRegions] = useState("");
  const [description, setDescription] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit =
    title.trim().length > 0 &&
    category.trim().length > 0 &&
    priceAmount.trim().length > 0 &&
    currency.trim().length === 3 &&
    countryCode.trim().length === 2 &&
    city.trim().length > 0 &&
    imageFile !== null &&
    !isSubmitting;

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    setError("");
    const nextFile = event.target.files?.[0] ?? null;
    if (nextFile === null) {
      setImageFile(null);
      return;
    }
    if (!SUPPORTED_IMAGE_TYPES.includes(nextFile.type as (typeof SUPPORTED_IMAGE_TYPES)[number])) {
      setImageFile(null);
      setError("Поддерживаются JPEG, PNG и WEBP до 10 MB.");
      return;
    }
    if (nextFile.size > MAX_IMAGE_BYTES) {
      setImageFile(null);
      setError("Поддерживаются JPEG, PNG и WEBP до 10 MB.");
      return;
    }
    setImageFile(nextFile);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!canSubmit || imageFile === null) {
      setError("Заполните обязательные поля и добавьте фото товара.");
      return;
    }

    setIsSubmitting(true);

    try {
      const client = new WebApiClient(getApiBaseUrl());
      const created = await client.createBusinessProduct({
        title: title.trim(),
        category: category.trim(),
        description: description.trim() || null,
        country_code: countryCode.trim().toUpperCase(),
        city: city.trim(),
        offer: {
          price_amount: priceAmount.trim(),
          currency: currency.trim().toUpperCase(),
          availability,
          delivery_regions: deliveryRegions.split(";").map((item) => item.trim()).filter(Boolean),
        },
      });
      const imagePayload = new FormData();
      imagePayload.append("file", imageFile);
      imagePayload.append("role", "primary");
      imagePayload.append("sort_order", "0");
      await client.uploadBusinessProductImage(created.product.product_id, imagePayload);
      setSuccess("Товар создан. Фото товара сохранено как primary image.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось создать товар.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Новый товар</p>
        <h1 className="workspace-page-title mt-4">Добавить товар в каталог</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Форма создаёт draft product через backend и сразу прикрепляет Фото товара. Публикация на маркетплейсы здесь
          не включена до реальных pipelines и подключенного магазина.
        </p>
      </section>

      <form className="mt-[50px] grid gap-5 xl:grid-cols-[1.1fr_0.9fr]" onSubmit={handleSubmit}>
        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Данные товара</h2>
          <div className="mt-6 grid gap-5">
            <label className="public-form-label grid gap-3">
              <span>Название товара</span>
              <input className="site-input" disabled={isSubmitting} onChange={(event) => setTitle(event.target.value)} value={title} />
            </label>
            <label className="public-form-label grid gap-3">
              <span>Категория</span>
              <input className="site-input" disabled={isSubmitting} onChange={(event) => setCategory(event.target.value)} value={category} />
            </label>
            <label className="public-form-label grid gap-3">
              <span>Описание</span>
              <textarea className="site-input min-h-28" disabled={isSubmitting} onChange={(event) => setDescription(event.target.value)} value={description} />
            </label>
            <div className="grid gap-5 md:grid-cols-2">
              <label className="public-form-label grid gap-3">
                <span>Цена</span>
                <input className="site-input" disabled={isSubmitting} inputMode="decimal" onChange={(event) => setPriceAmount(event.target.value)} value={priceAmount} />
              </label>
              <label className="public-form-label grid gap-3">
                <span>Валюта</span>
                <input className="site-input" disabled={isSubmitting} maxLength={3} onChange={(event) => setCurrency(event.target.value)} value={currency} />
              </label>
              <label className="public-form-label grid gap-3">
                <span>Страна</span>
                <input className="site-input" disabled={isSubmitting} maxLength={2} onChange={(event) => setCountryCode(event.target.value)} value={countryCode} />
              </label>
              <label className="public-form-label grid gap-3">
                <span>Город</span>
                <input className="site-input" disabled={isSubmitting} onChange={(event) => setCity(event.target.value)} value={city} />
              </label>
            </div>
            <label className="public-form-label grid gap-3">
              <span>Наличие</span>
              <select className="site-input" disabled={isSubmitting} onChange={(event) => setAvailability(event.target.value as BusinessProductAvailability)} value={availability}>
                <option value="in_stock">В наличии</option>
                <option value="out_of_stock">Нет в наличии</option>
                <option value="preorder">Предзаказ</option>
                <option value="unknown">Неизвестно</option>
              </select>
            </label>
            <label className="public-form-label grid gap-3">
              <span>Регионы доставки через ;</span>
              <input className="site-input" disabled={isSubmitting} onChange={(event) => setDeliveryRegions(event.target.value)} value={deliveryRegions} />
            </label>
          </div>
        </section>

        <section className="site-card p-7 lg:p-8">
          <h2 className="workspace-section-title">Фото товара</h2>
          <p className="workspace-body mt-4">Поддерживаются JPEG, PNG и WEBP до 10 MB.</p>
          <div className="mt-5 rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
            <p className="text-sm font-semibold text-[var(--text-primary)]">Upload requirements</p>
            <p className="workspace-body mt-2">
              Коротко: JPG, PNG, WEBP up to 10 MB. Для standard доступно до 10 фото на товар, для large до 30.
            </p>
            <details className="mt-3">
              <summary className="cursor-pointer text-sm font-semibold text-[var(--text-primary)]">
                Detailed upload limits
              </summary>
              <ul className="mt-3 grid gap-2 text-sm text-[var(--text-muted)]">
                <li>Основное фото товара обязательно перед отправкой на админ-проверку.</li>
                <li>Рекомендуется чистое фото товара без лишних объектов и водяных знаков.</li>
                <li>Фото должно показывать тот же тип одежды, который указан в категории.</li>
                <li>Если категория не совпадает с фото, товар не попадёт в поиск до исправления.</li>
                <li>Слишком много фото backend отклонит через business_catalog_backpressure.</li>
                <li>large-tier назначает администратор после проверки нагрузки магазина.</li>
              </ul>
            </details>
          </div>
          <label className="public-form-label mt-6 grid gap-3">
            <span>Фото товара</span>
            <input accept="image/jpeg,image/png,image/webp" disabled={isSubmitting} onChange={handleImageChange} type="file" />
          </label>
          {imageFile ? <p className="workspace-body mt-4">Выбран файл: {imageFile.name}</p> : null}
          {error ? <p className="mt-6 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
          {success ? <p className="mt-6 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">{success}</p> : null}
          <div className="mt-8 flex flex-wrap gap-3">
            <SiteButton disabled={!canSubmit} type="submit">
              {isSubmitting ? "Создаём товар" : "Создать товар"}
            </SiteButton>
            <SiteButton href="/workspace/business-catalog" variant="secondary">
              Вернуться в каталог
            </SiteButton>
          </div>
        </section>
      </form>
    </main>
  );
}
