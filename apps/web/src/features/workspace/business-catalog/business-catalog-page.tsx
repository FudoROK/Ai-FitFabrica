"use client";

import { useEffect, useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";
import type { BusinessMerchant, BusinessProduct } from "@/lib/api/business-catalog-contracts";

function formatCategoryValidationStatus(product: BusinessProduct): {
  label: string;
  toneClass: string;
  description: string;
} {
  if (product.category_validation_status === "matched") {
    return {
      label: "Категория совпала с фото",
      toneClass: "bg-emerald-50 text-emerald-800",
      description: product.visual_category
        ? `Backend определил: ${product.visual_category}${product.visual_category_confidence ? `, ${Math.round(product.visual_category_confidence * 100)}%` : ""}.`
        : "Товар может идти дальше на админ-проверку и индексацию.",
    };
  }
  if (product.category_validation_status === "mismatch") {
    return {
      label: "Категория не совпала с фото",
      toneClass: "bg-rose-50 text-rose-800",
      description: product.category_validation_reason ?? "Исправьте категорию или замените фото. До этого товар не попадёт в поиск.",
    };
  }
  if (product.category_validation_status === "uncertain") {
    return {
      label: "Нужна ручная проверка категории",
      toneClass: "bg-amber-50 text-amber-900",
      description: product.category_validation_reason ?? "Система не уверена в типе одежды. Админ должен проверить товар вручную.",
    };
  }
  return {
    label: "Категория ещё не проверена",
    toneClass: "bg-[var(--surface-alt)] text-[var(--text-primary)]",
    description: "Товар пока не готов к публичному поиску. Сначала нужна проверка категории по фото.",
  };
}

function formatSearchVisibility(product: BusinessProduct): {
  label: string;
  toneClass: string;
  description: string;
} {
  if (product.category_validation_status === "mismatch" || product.category_validation_status === "uncertain") {
    return {
      label: "Не попадёт в поиск",
      toneClass: "bg-rose-50 text-rose-800",
      description: "Сначала нужно исправить категорию или пройти ручную проверку администратора.",
    };
  }
  if (product.status === "rejected" || product.status === "archived") {
    return {
      label: "Не попадёт в поиск",
      toneClass: "bg-rose-50 text-rose-800",
      description: "Товар отклонён или отправлен в архив, поэтому не показывается пользователям.",
    };
  }
  if (product.review_status !== "approved") {
    return {
      label: "Ожидает админ-проверку",
      toneClass: "bg-amber-50 text-amber-900",
      description: "Товар сохранён, но ещё не одобрен администратором для локального поиска.",
    };
  }
  if (product.search_index_status !== "indexed") {
    return {
      label: "Индексация ещё не завершена",
      toneClass: "bg-amber-50 text-amber-900",
      description: "Товар одобрен, но поисковый индекс ещё не готов. Если статус failed, нужна повторная индексация.",
    };
  }
  return {
    label: "Доступен в локальном поиске",
    toneClass: "bg-emerald-50 text-emerald-800",
    description: "Пользователи могут увидеть этот товар в Similar Search, если он похож на загруженную одежду.",
  };
}

export function BusinessCatalogPage() {
  const [merchant, setMerchant] = useState<BusinessMerchant | null>(null);
  const [products, setProducts] = useState<BusinessProduct[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    async function loadCatalog() {
      setIsLoading(true);
      setError("");

      try {
        const client = new WebApiClient(getApiBaseUrl());
        const [merchantResponse, productsResponse] = await Promise.all([
          client.getBusinessMerchant(),
          client.listBusinessProducts(),
        ]);
        if (!isActive) {
          return;
        }
        setMerchant(merchantResponse.merchant);
        setProducts(productsResponse.products);
      } catch (requestError) {
        if (!isActive) {
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить каталог товаров.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadCatalog();

    return () => {
      isActive = false;
    };
  }, []);

  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">B2B каталог</p>
        <h1 className="workspace-page-title mt-4">Каталог товаров</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Управляйте товарами, ценами, городом продажи и черновиками карточек. Данные идут через backend API и не
          смешиваются с будущим публичным поиском до админ-проверки.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <SiteButton href="/workspace/business-catalog/new" icon="add">
            Добавить товар
          </SiteButton>
          <SiteButton href="/workspace/business-catalog/import" variant="secondary">
            Импорт CSV-файла
          </SiteButton>
        </div>
      </section>

      <section className="mt-[50px] grid gap-5">
        {isLoading ? (
          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-section-title">Загрузка каталога</h2>
            <p className="workspace-body mt-4">Получаем бизнес-профиль и список товаров из backend.</p>
          </article>
        ) : null}

        {!isLoading && error ? (
          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-section-title">Не удалось загрузить каталог</h2>
            <p className="workspace-body mt-4">{error}</p>
            <div className="mt-6">
              <SiteButton href="/workspace/business-profile" variant="secondary">
                Проверить бизнес-профиль
              </SiteButton>
            </div>
          </article>
        ) : null}

        {!isLoading && !error && products.length === 0 ? (
          <article className="site-card p-7 lg:p-8">
            <h2 className="workspace-section-title">Пока нет товаров</h2>
            <p className="workspace-body mt-4">
              {merchant
                ? "Создайте первый товар вручную или загрузите CSV-файл."
                : "Сначала сохраните бизнес-профиль, затем добавляйте товары."}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <SiteButton href="/workspace/business-catalog/new">Создать товар</SiteButton>
              <SiteButton href="/workspace/business-profile" variant="secondary">
                Бизнес-профиль
              </SiteButton>
            </div>
          </article>
        ) : null}

        {!isLoading && !error && products.length > 0 ? (
          <div className="grid gap-4 xl:grid-cols-2">
            {products.map((product) => (
              <article className="site-card p-7" key={product.product_id}>
                {(() => {
                  const categoryStatus = formatCategoryValidationStatus(product);
                  const searchVisibility = formatSearchVisibility(product);
                  return (
                    <>
                      <p className="eyebrow">{product.status} · {product.review_status}</p>
                      <p className="eyebrow mt-2">search index: {product.search_index_status}</p>
                      {product.search_index_error ? <p className="workspace-error mt-2">{product.search_index_error}</p> : null}
                      <h2 className="workspace-card-title mt-3">{product.title}</h2>
                      <p className="workspace-body mt-4">
                        {product.category} · {product.country_code}, {product.city}
                      </p>
                      <div className="mt-4 rounded-[1.25rem] border border-[var(--border)] bg-white/70 p-4">
                        <p className="workspace-meta font-semibold">Проверка категории</p>
                        <span className={`mt-3 inline-flex rounded-full px-3 py-1 text-xs font-semibold ${categoryStatus.toneClass}`}>
                          {categoryStatus.label}
                        </span>
                        <p className="workspace-body mt-3">{categoryStatus.description}</p>
                      </div>
                      <div className="mt-4 rounded-[1.25rem] border border-[var(--border)] bg-white/70 p-4">
                        <p className="workspace-meta font-semibold">Видимость в поиске</p>
                        <span className={`mt-3 inline-flex rounded-full px-3 py-1 text-xs font-semibold ${searchVisibility.toneClass}`}>
                          {searchVisibility.label}
                        </span>
                        <p className="workspace-body mt-3">{searchVisibility.description}</p>
                      </div>
                      {product.description ? <p className="workspace-body mt-3">{product.description}</p> : null}
                    </>
                  );
                })()}
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}
