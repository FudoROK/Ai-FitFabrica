"use client";

import { useState } from "react";
import type {
  AdminBusinessCatalogCredentials,
  AdminBulkApproveBusinessCatalogProductItem,
  AdminBulkValidateBusinessCatalogProductCategoryItem,
  BusinessProduct,
  BusinessProductSearchIndexStatus,
  SimilarSearchClickAnalyticsResponse,
} from "@/lib/api/business-catalog-contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

type ReviewState = "loading" | "ready" | "empty" | "error" | "locked";
type SearchIndexFilter = "all" | BusinessProductSearchIndexStatus;
type ReviewFilter = "all" | "ready_to_approve" | "needs_ai_validation" | "blocked_by_category" | "indexing_issues";
type ProductReviewReadiness = {
  status: "ready" | "blocked" | "attention";
  title: string;
  nextAction: string;
};
type ProductReviewSummary = {
  total: number;
  readyToApprove: number;
  needsAiValidation: number;
  blockedByCategory: number;
  indexingIssues: number;
};
type BulkOperationItem =
  | AdminBulkValidateBusinessCatalogProductCategoryItem
  | AdminBulkApproveBusinessCatalogProductItem;
type BulkOperationDetails = {
  operation: "category_validation" | "approve_matched";
  items: BulkOperationItem[];
};

const ADMIN_UI_ENABLED = process.env.NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI === "true";

export function getBusinessProductReviewReadiness(product: BusinessProduct): ProductReviewReadiness {
  if (product.search_index_status === "failed") {
    return {
      status: "attention",
      title: "Search indexing failed",
      nextAction: "Retry search indexing after checking the backend error.",
    };
  }
  if (product.category_validation_status === "not_checked") {
    return {
      status: "blocked",
      title: "Category is not checked",
      nextAction: "Run AI validation before approval.",
    };
  }
  if (product.category_validation_status === "mismatch") {
    return {
      status: "blocked",
      title: "Category mismatch",
      nextAction: "Fix category mismatch or reject/archive the product.",
    };
  }
  if (product.category_validation_status === "uncertain") {
    return {
      status: "blocked",
      title: "Category is uncertain",
      nextAction: "Run AI validation again or save a manual visual category check.",
    };
  }
  if (product.review_status === "approved" || product.status === "active") {
    return {
      status: "ready",
      title: "Already approved",
      nextAction: "Wait for search indexing if the product is still pending.",
    };
  }
  return {
    status: "ready",
    title: "Ready for review",
    nextAction: "Product is ready for approve.",
  };
}

export function getBusinessProductReviewSummary(products: BusinessProduct[]): ProductReviewSummary {
  return products.reduce<ProductReviewSummary>(
    (summary, product) => {
      const categoryStatus = product.category_validation_status;
      return {
        total: summary.total + 1,
        readyToApprove: summary.readyToApprove + (categoryStatus === "matched" ? 1 : 0),
        needsAiValidation: summary.needsAiValidation + (categoryStatus === "not_checked" ? 1 : 0),
        blockedByCategory:
          summary.blockedByCategory + (categoryStatus === "mismatch" || categoryStatus === "uncertain" ? 1 : 0),
        indexingIssues: summary.indexingIssues + (product.search_index_status === "failed" ? 1 : 0),
      };
    },
    {
      total: 0,
      readyToApprove: 0,
      needsAiValidation: 0,
      blockedByCategory: 0,
      indexingIssues: 0,
    },
  );
}

export function matchesBusinessProductReviewFilter(product: BusinessProduct, filter: ReviewFilter): boolean {
  if (filter === "ready_to_approve") {
    return product.category_validation_status === "matched";
  }
  if (filter === "needs_ai_validation") {
    return product.category_validation_status === "not_checked";
  }
  if (filter === "blocked_by_category") {
    return product.category_validation_status === "mismatch" || product.category_validation_status === "uncertain";
  }
  if (filter === "indexing_issues") {
    return product.search_index_status === "failed";
  }
  return true;
}

export function getStatusBadgeTone(value: string): string {
  if (["matched", "indexed", "approved", "active", "validated"].includes(value)) {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (["mismatch", "failed", "rejected"].includes(value)) {
    return "border-rose-200 bg-rose-50 text-rose-800";
  }
  if (["uncertain", "pending", "not_checked"].includes(value)) {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }
  return "border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text-primary)]";
}

export function AdminBusinessCatalogReview() {
  const [adminToken, setAdminToken] = useState("");
  const [error, setError] = useState("");
  const [products, setProducts] = useState<BusinessProduct[]>([]);
  const [similarSearchAnalytics, setSimilarSearchAnalytics] = useState<SimilarSearchClickAnalyticsResponse | null>(null);
  const [rejectReasons, setRejectReasons] = useState<Record<string, string>>({});
  const [categoryValidationInputs, setCategoryValidationInputs] = useState<
    Record<string, { confidence: string; visualCategory: string }>
  >({});
  const [bulkValidationLimit, setBulkValidationLimit] = useState("10");
  const [bulkValidationSummary, setBulkValidationSummary] = useState("");
  const [bulkApproveLimit, setBulkApproveLimit] = useState("10");
  const [bulkApproveSummary, setBulkApproveSummary] = useState("");
  const [lastBulkOperation, setLastBulkOperation] = useState<BulkOperationDetails | null>(null);
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>("all");
  const [searchIndexFilter, setSearchIndexFilter] = useState<SearchIndexFilter>("all");
  const [state, setState] = useState<ReviewState>(ADMIN_UI_ENABLED ? "empty" : "locked");
  const [submittingProductId, setSubmittingProductId] = useState<string | null>(null);

  const canLoad = ADMIN_UI_ENABLED && adminToken.trim().length > 0;
  const credentials: AdminBusinessCatalogCredentials = {
    adminToken: adminToken.trim(),
  };
  const reviewSummary = getBusinessProductReviewSummary(products);
  const visibleProducts = products.filter(
    (product) =>
      matchesBusinessProductReviewFilter(product, reviewFilter) &&
      (searchIndexFilter === "all" || product.search_index_status === searchIndexFilter),
  );

  async function loadProducts() {
    if (!canLoad) {
      setProducts([]);
      setState(ADMIN_UI_ENABLED ? "empty" : "locked");
      return;
    }
    setState("loading");
    setError("");
    try {
      const client = apiClient();
      const [response, analytics] = await Promise.all([
        client.getAdminBusinessCatalogPendingProducts(credentials),
        client.getAdminSimilarSearchAnalytics(credentials),
      ]);
      setProducts(response.products);
      setSimilarSearchAnalytics(analytics);
      setState(response.products.length > 0 ? "ready" : "empty");
    } catch (requestError) {
      setProducts([]);
      setSimilarSearchAnalytics(null);
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить товары на проверку.");
      setState("error");
    }
  }

  async function approve(productId: string) {
    await mutate(productId, () => apiClient().approveAdminBusinessCatalogProduct(productId, credentials));
  }

  async function reject(productId: string) {
    const reason = rejectReasons[productId]?.trim() ?? "";
    if (!reason) {
      setError("Укажите причину отклонения товара.");
      setState("error");
      return;
    }
    await mutate(productId, () => apiClient().rejectAdminBusinessCatalogProduct(productId, { reason }, credentials));
  }

  async function archiveProduct(productId: string) {
    await mutate(productId, () => apiClient().archiveAdminBusinessCatalogProduct(productId, credentials));
  }

  async function validateCategory(productId: string) {
    const input = categoryValidationInputs[productId] ?? { confidence: "", visualCategory: "" };
    const visualCategory = input.visualCategory.trim();
    const confidence = Number(input.confidence);
    if (!visualCategory || !Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
      setError("Category validation requires visual category and confidence from 0 to 1.");
      setState("error");
      return;
    }
    await mutate(productId, () =>
      apiClient().validateAdminBusinessCatalogProductCategory(
        productId,
        {
          confidence,
          visual_category: visualCategory,
        },
        credentials,
      ),
    );
  }

  async function runCategoryValidation(productId: string) {
    await mutate(productId, () => apiClient().runAdminBusinessCatalogProductCategoryValidation(productId, credentials));
  }

  async function runCategoryValidationBatch() {
    const limit = Number(bulkValidationLimit);
    if (!Number.isInteger(limit) || limit < 1 || limit > 25) {
      setError("Bulk validation limit must be an integer from 1 to 25.");
      setState("error");
      return;
    }
    setSubmittingProductId("__bulk_category_validation__");
    setError("");
    setBulkValidationSummary("");
    setLastBulkOperation(null);
    try {
      const response = await apiClient().runAdminBusinessCatalogProductCategoryValidationBatch({ limit }, credentials);
      setBulkValidationSummary(
        `Processed ${response.result.processed_count}: ${response.result.validated_count} validated, ${response.result.failed_count} failed.`,
      );
      setLastBulkOperation({ operation: "category_validation", items: response.result.items });
      await loadProducts();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Bulk category validation failed.");
      setState("error");
    } finally {
      setSubmittingProductId(null);
    }
  }

  async function approveMatchedBatch() {
    const limit = Number(bulkApproveLimit);
    if (!Number.isInteger(limit) || limit < 1 || limit > 25) {
      setError("Bulk approve limit must be an integer from 1 to 25.");
      setState("error");
      return;
    }
    setSubmittingProductId("__bulk_approve_matched__");
    setError("");
    setBulkApproveSummary("");
    setLastBulkOperation(null);
    try {
      const response = await apiClient().approveAdminBusinessCatalogMatchedProductBatch({ limit }, credentials);
      setBulkApproveSummary(
        `Processed ${response.result.processed_count}: ${response.result.approved_count} approved, ${response.result.failed_count} failed.`,
      );
      setLastBulkOperation({ operation: "approve_matched", items: response.result.items });
      await loadProducts();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Bulk approve failed.");
      setState("error");
    } finally {
      setSubmittingProductId(null);
    }
  }

  async function retrySearchIndex(productId: string) {
    await mutate(productId, () => apiClient().retryAdminBusinessCatalogProductSearchIndex(productId, credentials));
  }

  async function mutate(productId: string, operation: () => Promise<{ product: BusinessProduct }>) {
    setSubmittingProductId(productId);
    setError("");
    try {
      await operation();
      await loadProducts();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось выполнить действие.");
      setState("error");
    } finally {
      setSubmittingProductId(null);
    }
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-8 lg:px-10 lg:py-12">
      <section className="site-card mx-auto max-w-[1180px] p-8 lg:p-10">
        <p className="eyebrow">Admin Business Catalog</p>
        <h1 className="workspace-page-title mt-4">Проверка товаров бизнес-каталога</h1>
        <p className="workspace-page-lead mt-4 max-w-[900px]">
          Здесь администратор вручную проверяет товары продавцов перед попаданием в каталог поиска.
          Пользовательский кабинет не может сам одобрять товары: approve и reject проходят только через backend.
        </p>

        {state === "locked" ? (
          <StatusPanel
            title="Админ-панель выключена"
            message="Включите NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI=true только для внутреннего окружения."
          />
        ) : (
          <div className="mt-8 grid gap-4 rounded-[28px] border border-[var(--border)] bg-white/80 p-5 lg:grid-cols-[1fr_auto]">
            <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
              Admin access token
              <input
                className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--text-primary)]"
                onChange={(event) => setAdminToken(event.target.value)}
                placeholder="Paste admin access token"
                type="password"
                value={adminToken}
              />
            </label>
            <button
              className="self-end rounded-full bg-[var(--text-primary)] px-6 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
              disabled={!canLoad || state === "loading"}
              onClick={() => void loadProducts()}
              type="button"
            >
              Загрузить товары
            </button>
          </div>
        )}
      </section>

      <section className="mx-auto mt-8 max-w-[1180px]">
        {state === "loading" ? <StatusPanel title="loading" message="Загружаю товары из backend." /> : null}
        {state === "empty" ? (
          <StatusPanel title="empty" message="Нет товаров на проверке или не указан admin actor id." />
        ) : null}
        {state === "error" ? <StatusPanel title="error" message={error} /> : null}
        {similarSearchAnalytics ? <SimilarSearchAnalyticsPanel analytics={similarSearchAnalytics} /> : null}
        {state === "ready" ? (
          <div className="grid gap-5">
            <ReviewQueueSummaryPanel summary={reviewSummary} />
            <AdminOperationOrderPanel />
            {lastBulkOperation ? (
              <BulkOperationDetailsPanel details={lastBulkOperation} onClear={() => setLastBulkOperation(null)} />
            ) : null}
            <div className="site-card p-5">
              <p className="eyebrow">Bulk Category Validation</p>
              <p className="workspace-body mt-2">
                Run AI category validation for pending products before approve. Limit is capped to protect AI spend.
              </p>
              <div className="mt-4 grid gap-3 md:grid-cols-[180px_auto_1fr]">
                <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                  Limit
                  <input
                    className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                    inputMode="numeric"
                    onChange={(event) => setBulkValidationLimit(event.target.value)}
                    value={bulkValidationLimit}
                  />
                </label>
                <button
                  className="self-end rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={submittingProductId === "__bulk_category_validation__"}
                  onClick={() => void runCategoryValidationBatch()}
                  type="button"
                >
                  Run AI validation batch
                </button>
                {bulkValidationSummary ? <p className="workspace-body self-end">{bulkValidationSummary}</p> : null}
              </div>
            </div>
            <div className="site-card p-5">
              <p className="eyebrow">Bulk Approve</p>
              <p className="workspace-body mt-2">
                Approve only pending products that already have matched category validation. Search indexing is queued by backend.
              </p>
              <div className="mt-4 grid gap-3 md:grid-cols-[180px_auto_1fr]">
                <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                  Limit
                  <input
                    className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                    inputMode="numeric"
                    onChange={(event) => setBulkApproveLimit(event.target.value)}
                    value={bulkApproveLimit}
                  />
                </label>
                <button
                  className="self-end rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={submittingProductId === "__bulk_approve_matched__"}
                  onClick={() => void approveMatchedBatch()}
                  type="button"
                >
                  Approve matched batch
                </button>
                {bulkApproveSummary ? <p className="workspace-body self-end">{bulkApproveSummary}</p> : null}
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                Review filter
                <select
                  className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-base outline-none"
                  onChange={(event) => setReviewFilter(event.target.value as ReviewFilter)}
                  value={reviewFilter}
                >
                  <option value="all">all</option>
                  <option value="ready_to_approve">ready_to_approve</option>
                  <option value="needs_ai_validation">needs_ai_validation</option>
                  <option value="blocked_by_category">blocked_by_category</option>
                  <option value="indexing_issues">indexing_issues</option>
                </select>
              </label>
              <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                Search index filter
                <select
                  className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-base outline-none"
                  onChange={(event) => setSearchIndexFilter(event.target.value as SearchIndexFilter)}
                  value={searchIndexFilter}
                >
                  <option value="all">all</option>
                  <option value="not_indexed">not_indexed</option>
                  <option value="pending">pending</option>
                  <option value="indexed">indexed</option>
                  <option value="failed">failed</option>
                </select>
              </label>
            </div>
            {visibleProducts.length === 0 ? (
              <StatusPanel title="no matching products" message="No products match the selected review filters." />
            ) : null}
            {visibleProducts.map((product) => {
              const isSubmitting = submittingProductId === product.product_id;
              const validationInput = categoryValidationInputs[product.product_id] ?? {
                confidence: product.visual_category_confidence?.toString() ?? "",
                visualCategory: product.visual_category ?? "",
              };
              const canApprove = product.category_validation_status === "matched";
              const reviewReadiness = getBusinessProductReviewReadiness(product);
              return (
                <article className="site-card p-6" key={product.product_id}>
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <StatusBadge value={product.review_status} />
                      <h2 className="workspace-card-title mt-3">{product.title}</h2>
                      <p className="workspace-body mt-3">
                        Категория: <strong>{product.category}</strong> · Город:{" "}
                        <strong>
                          {product.country_code}, {product.city}
                        </strong>{" "}
                        · Status: <strong>{product.status}</strong>
                      </p>
                      <p className="workspace-body mt-2">
                        Search index: <StatusBadge value={product.search_index_status} />
                      </p>
                      <p className="workspace-body mt-2">
                        Category validation: <StatusBadge value={product.category_validation_status} />
                        {product.visual_category ? (
                          <>
                            {" "}
                            - visual: <strong>{product.visual_category}</strong>
                          </>
                        ) : null}
                      </p>
                      {product.category_validation_reason ? (
                        <p className="workspace-body mt-2">{product.category_validation_reason}</p>
                      ) : null}
                      {product.search_index_error ? (
                        <p className="workspace-error mt-2">{product.search_index_error}</p>
                      ) : null}
                      <div className="mt-4 rounded-[22px] border border-[var(--border)] bg-white/80 p-4">
                        <p className="workspace-meta">Review readiness</p>
                        <p className="mt-2 text-sm font-semibold text-[var(--text-primary)]">
                          {reviewReadiness.title}
                        </p>
                        <p className="workspace-body mt-2">{reviewReadiness.nextAction}</p>
                      </div>
                      {product.search_index_status === "failed" ? (
                        <button
                          className="mt-4 rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                          disabled={isSubmitting}
                          onClick={() => void retrySearchIndex(product.product_id)}
                          type="button"
                        >
                          Retry search indexing
                        </button>
                      ) : null}
                    </div>
                    <button
                      className="rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={isSubmitting || !canApprove}
                      onClick={() => void approve(product.product_id)}
                      type="button"
                    >
                      Approve
                    </button>
                    <button
                      className="rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={isSubmitting}
                      onClick={() => void archiveProduct(product.product_id)}
                      type="button"
                    >
                      Archive
                    </button>
                  </div>

                  <p className="workspace-body mt-5">{product.description || "Описание не заполнено."}</p>
                  {product.review_reason ? (
                    <p className="workspace-body mt-3">Текущая причина проверки: {product.review_reason}</p>
                  ) : null}

                  <div className="mt-6 rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
                    <p className="text-sm font-semibold text-[var(--text-primary)]">Category validation gate</p>
                    <p className="workspace-body mt-2">
                      Approve is locked until backend stores a matched visual category check.
                    </p>
                    <button
                      className="mt-4 rounded-full bg-[var(--text-primary)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={isSubmitting}
                      onClick={() => void runCategoryValidation(product.product_id)}
                      type="button"
                    >
                      Run AI validation
                    </button>
                    <div className="mt-4 grid gap-3 md:grid-cols-[1fr_160px_auto]">
                      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                        Visual category
                        <input
                          className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                          onChange={(event) =>
                            setCategoryValidationInputs((current) => ({
                              ...current,
                              [product.product_id]: {
                                ...validationInput,
                                visualCategory: event.target.value,
                              },
                            }))
                          }
                          placeholder="shirt, outerwear, pants"
                          value={validationInput.visualCategory}
                        />
                      </label>
                      <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                        Confidence
                        <input
                          className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                          inputMode="decimal"
                          onChange={(event) =>
                            setCategoryValidationInputs((current) => ({
                              ...current,
                              [product.product_id]: {
                                ...validationInput,
                                confidence: event.target.value,
                              },
                            }))
                          }
                          placeholder="0.94"
                          value={validationInput.confidence}
                        />
                      </label>
                      <button
                        className="self-end rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={isSubmitting}
                        onClick={() => void validateCategory(product.product_id)}
                        type="button"
                      >
                        Save validation
                      </button>
                    </div>
                  </div>

                  <div className="mt-6 rounded-[24px] border border-[var(--border)] bg-white/70 p-4">
                    <label className="grid gap-2 text-sm font-semibold text-[var(--text-primary)]">
                      Причина отклонения
                      <input
                        className="rounded-2xl border border-[var(--border)] px-4 py-3 outline-none"
                        onChange={(event) =>
                          setRejectReasons((current) => ({ ...current, [product.product_id]: event.target.value }))
                        }
                        placeholder="Например: нет фото товара или неверная категория"
                        value={rejectReasons[product.product_id] ?? ""}
                      />
                    </label>
                    <button
                      className="mt-4 rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={isSubmitting}
                      onClick={() => void reject(product.product_id)}
                      type="button"
                    >
                      Reject
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : null}
      </section>
    </main>
  );
}

function StatusPanel({ message, title }: { message: string; title: string }) {
  return (
    <div className="site-card p-8">
      <p className="eyebrow">{title}</p>
      <p className="workspace-body mt-4">{message}</p>
    </div>
  );
}

function SimilarSearchAnalyticsPanel({ analytics }: { analytics: SimilarSearchClickAnalyticsResponse }) {
  return (
    <section className="site-card mb-8 p-6">
      <p className="eyebrow">Similar Search Analytics</p>
      <h2 className="workspace-card-title mt-3">Free search click performance</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <MetricCard label="Total clicks" value={analytics.summary.total_clicks} />
        <MetricCard label="External redirects" value={analytics.summary.redirect_clicks} />
        <MetricCard label="Local-only clicks" value={analytics.summary.local_only_clicks} />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <AnalyticsList items={analytics.top_products} title="Top products" />
        <AnalyticsList items={analytics.top_marketplaces} title="Top marketplaces" />
        <AnalyticsList items={analytics.top_cities} title="Top cities" />
      </div>
    </section>
  );
}

function ReviewQueueSummaryPanel({ summary }: { summary: ProductReviewSummary }) {
  return (
    <section className="site-card p-6">
      <p className="eyebrow">Review queue summary</p>
      <h2 className="workspace-card-title mt-3">Admin workload</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Total pending" value={summary.total} />
        <MetricCard label="Ready to approve" value={summary.readyToApprove} />
        <MetricCard label="Needs AI validation" value={summary.needsAiValidation} />
        <MetricCard label="Blocked by category" value={summary.blockedByCategory} />
        <MetricCard label="Indexing issues" value={summary.indexingIssues} />
      </div>
    </section>
  );
}

function AdminOperationOrderPanel() {
  return (
    <section className="site-card p-6">
      <p className="eyebrow">Admin operation order</p>
      <h2 className="workspace-card-title mt-3">Safe catalog review sequence</h2>
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <InstructionCard
          title="1. Run AI validation batch"
          body="Validate product photos against declared categories before any approval action."
        />
        <InstructionCard
          title="2. Approve matched batch"
          body="Approve only products with matched category validation. Do not approve mismatched or uncertain products."
        />
        <InstructionCard
          title="3. Check indexing status"
          body="Products should move to indexed after worker processing. Retry only failed indexing records."
        />
      </div>
    </section>
  );
}

function BulkOperationDetailsPanel({ details, onClear }: { details: BulkOperationDetails; onClear: () => void }) {
  const operationLabel =
    details.operation === "category_validation" ? "category validation batch" : "approve matched batch";
  return (
    <section className="site-card p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="eyebrow">Bulk operation details</p>
          <h2 className="workspace-card-title mt-3">{operationLabel}</h2>
        </div>
        <button
          className="rounded-full border border-[var(--border)] px-5 py-3 text-sm font-semibold"
          onClick={onClear}
          type="button"
        >
          Clear bulk result
        </button>
      </div>
      {details.items.length === 0 ? (
        <p className="workspace-body mt-4">No product_id items were returned for this operation.</p>
      ) : null}
      <div className="mt-5 grid gap-3">
        {details.items.map((item) => (
          <div
            className="rounded-[18px] border border-[var(--border)] bg-white/75 p-4"
            key={`${details.operation}-${item.product_id}`}
          >
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <p className="text-sm font-semibold text-[var(--text-primary)]">product_id: {item.product_id}</p>
              <StatusBadge value={item.status} />
            </div>
            {item.error_message ? <p className="workspace-error mt-2">error_message: {item.error_message}</p> : null}
          </div>
        ))}
      </div>
    </section>
  );
}

function InstructionCard({ body, title }: { body: string; title: string }) {
  return (
    <div className="rounded-[22px] border border-[var(--border)] bg-white/75 p-4">
      <p className="text-sm font-semibold text-[var(--text-primary)]">{title}</p>
      <p className="workspace-body mt-2">{body}</p>
    </div>
  );
}

function StatusBadge({ label, value }: { label?: string; value: string }) {
  return (
    <span
      className={`inline-flex w-fit items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold ${getStatusBadgeTone(value)}`}
    >
      {label ? <span>{label}:</span> : null}
      <span>{value}</span>
    </span>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-[22px] border border-[var(--border)] bg-white/75 p-4">
      <p className="workspace-meta">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-[var(--text-primary)]">{value.toLocaleString("ru-RU")}</p>
    </div>
  );
}

function AnalyticsList({ items, title }: { items: SimilarSearchClickAnalyticsResponse["top_products"]; title: string }) {
  return (
    <div className="rounded-[22px] border border-[var(--border)] bg-white/75 p-4">
      <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">{title}</h3>
      {items.length === 0 ? <p className="workspace-meta mt-4">No click data yet.</p> : null}
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div className="flex items-start justify-between gap-3" key={`${title}-${item.key}`}>
            <p className="text-sm font-semibold text-[var(--text-primary)]">{item.label}</p>
            <p className="rounded-full bg-[var(--surface-alt)] px-3 py-1 text-xs font-semibold text-[var(--text-primary)]">
              {item.click_count}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function apiClient(): WebApiClient {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("Admin API base URL is not configured.");
  }
  return new WebApiClient(baseUrl);
}
