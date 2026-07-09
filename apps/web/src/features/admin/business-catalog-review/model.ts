import type { BusinessProduct } from "@/lib/api/business-catalog-contracts";
import type { ProductReviewReadiness, ProductReviewSummary, ReviewFilter } from "./types";

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
