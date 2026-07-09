import type {
  AdminBulkApproveBusinessCatalogProductItem,
  AdminBulkValidateBusinessCatalogProductCategoryItem,
  AdminMarketplaceDiscoveryCandidateSourceType,
  AdminMarketplaceDiscoveryCandidateStatus,
  BusinessProductSearchIndexStatus,
} from "@/lib/api/business-catalog-contracts";

export type ReviewState = "loading" | "ready" | "empty" | "error" | "locked";
export type SearchIndexFilter = "all" | BusinessProductSearchIndexStatus;
export type ReviewFilter = "all" | "ready_to_approve" | "needs_ai_validation" | "blocked_by_category" | "indexing_issues";
export type DiscoveryCandidateFilters = {
  category: string;
  city: string;
  sourceType: "all" | AdminMarketplaceDiscoveryCandidateSourceType;
  status: "all" | AdminMarketplaceDiscoveryCandidateStatus;
};
export type CategoryValidationInput = {
  confidence: string;
  visualCategory: string;
};
export type ProductReviewReadiness = {
  status: "ready" | "blocked" | "attention";
  title: string;
  nextAction: string;
};
export type ProductReviewSummary = {
  total: number;
  readyToApprove: number;
  needsAiValidation: number;
  blockedByCategory: number;
  indexingIssues: number;
};
export type BulkOperationItem =
  | AdminBulkValidateBusinessCatalogProductCategoryItem
  | AdminBulkApproveBusinessCatalogProductItem;
export type BulkOperationDetails = {
  operation: "category_validation" | "approve_matched";
  items: BulkOperationItem[];
};
