export type BusinessMerchantStatus = "draft" | "submitted" | "active" | "suspended";

export type BusinessProductStatus = "draft" | "submitted" | "active" | "rejected" | "archived";

export type BusinessProductReviewStatus = "not_required" | "pending" | "approved" | "rejected";

export type BusinessProductSearchIndexStatus = "not_indexed" | "pending" | "indexed" | "failed";

export type BusinessProductCategoryValidationStatus = "not_checked" | "matched" | "mismatch" | "uncertain";

export type BusinessProductAvailability = "in_stock" | "out_of_stock" | "preorder" | "unknown";

export type BusinessProductImageRole = "primary" | "gallery" | "source" | "generated";

export type BusinessCatalogImportStatus =
  | "uploaded"
  | "validating"
  | "completed"
  | "completed_with_errors"
  | "failed";

export type BusinessCatalogTenantTier = "standard" | "large";

export type AdminMarketplaceDiscoveryCandidateStatus =
  | "pending"
  | "needs_review"
  | "approved"
  | "rejected"
  | "archived";

export type AdminMarketplaceDiscoveryCandidateSourceType =
  | "instagram"
  | "open_web"
  | "manual"
  | "other"
  | "local_catalog"
  | "partner_feed"
  | "official_api"
  | "seller_connected_store"
  | "admin_verified_link"
  | "instagram_business"
  | "public_web_allowed"
  | "search_engine_discovery"
  | "instagram_public_discovery";

export type BusinessMerchant = {
  merchant_id: string;
  owner_id: string;
  display_name: string;
  legal_name?: string | null;
  country_code: string;
  city: string;
  contact_email?: string | null;
  instagram_url?: string | null;
  website_url?: string | null;
  status: BusinessMerchantStatus;
  created_at: string;
  updated_at: string;
};

export type BusinessMerchantPayload = {
  display_name: string;
  legal_name?: string | null;
  country_code: string;
  city: string;
  contact_email?: string | null;
  instagram_url?: string | null;
  website_url?: string | null;
};

export type BusinessMerchantResponse = {
  merchant: BusinessMerchant;
};

export type BusinessProductOfferPayload = {
  price_amount: string;
  currency: string;
  availability: BusinessProductAvailability;
  product_url?: string | null;
  delivery_regions: string[];
};

export type BusinessProductCreatePayload = {
  title: string;
  category: string;
  description?: string | null;
  country_code: string;
  city: string;
  offer: BusinessProductOfferPayload;
  source_type?: string;
};

export type BusinessProduct = {
  product_id: string;
  merchant_id: string;
  owner_id: string;
  title: string;
  category: string;
  description?: string | null;
  country_code: string;
  city: string;
  status: BusinessProductStatus;
  review_status: BusinessProductReviewStatus;
  source_type: string;
  review_reason?: string | null;
  category_validation_status: BusinessProductCategoryValidationStatus;
  category_validation_reason?: string | null;
  visual_category?: string | null;
  visual_category_confidence?: number | null;
  category_validated_at?: string | null;
  search_index_status: BusinessProductSearchIndexStatus;
  search_index_error?: string | null;
  search_indexed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type BusinessProductResponse = {
  product: BusinessProduct;
};

export type BusinessProductListResponse = {
  products: BusinessProduct[];
};

export type AdminBusinessCatalogCredentials = {
  adminToken: string;
};

export type AdminBusinessCatalogPendingProductsResponse = {
  products: BusinessProduct[];
};

export type AdminMarketplaceDiscoveryCandidate = {
  candidate_id: string;
  workspace_id?: string | null;
  business_id?: string | null;
  connector_kind: string;
  source_type: AdminMarketplaceDiscoveryCandidateSourceType;
  source_url: string;
  image_url?: string | null;
  media_url?: string | null;
  source_title: string;
  title?: string | null;
  name?: string | null;
  brand?: string | null;
  source_snippet?: string | null;
  platform_hint?: string | null;
  category?: string | null;
  country_code?: string | null;
  city?: string | null;
  price_amount?: number | null;
  currency?: string | null;
  raw_payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
  status: AdminMarketplaceDiscoveryCandidateStatus;
  rejection_reason?: string | null;
  approved_at?: string | null;
  rejected_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminMarketplaceDiscoveryCandidateFilters = {
  status?: AdminMarketplaceDiscoveryCandidateStatus;
  source_type?: AdminMarketplaceDiscoveryCandidateSourceType;
  category?: string;
  city?: string;
  limit?: number;
};

export type AdminMarketplaceDiscoveryCandidateListResponse = {
  candidates: AdminMarketplaceDiscoveryCandidate[];
};

export type AdminMarketplaceDiscoveryCandidateMutationResponse = {
  candidate: AdminMarketplaceDiscoveryCandidate;
};

export type AdminRejectMarketplaceDiscoveryCandidatePayload = {
  reason?: string | null;
};

export type AdminRejectBusinessCatalogProductPayload = {
  reason: string;
};

export type AdminValidateBusinessCatalogProductCategoryPayload = {
  visual_category: string;
  confidence: number;
};

export type AdminBulkValidateBusinessCatalogProductCategoryPayload = {
  limit: number;
};

export type AdminBulkValidateBusinessCatalogProductCategoryItem = {
  product_id: string;
  status: "validated" | "failed";
  product?: BusinessProduct | null;
  error_message?: string | null;
};

export type AdminBulkValidateBusinessCatalogProductCategoryResult = {
  requested_limit: number;
  processed_count: number;
  validated_count: number;
  failed_count: number;
  items: AdminBulkValidateBusinessCatalogProductCategoryItem[];
};

export type AdminBulkValidateBusinessCatalogProductCategoryResponse = {
  result: AdminBulkValidateBusinessCatalogProductCategoryResult;
};

export type AdminBulkApproveBusinessCatalogProductPayload = {
  limit: number;
};

export type AdminBulkApproveBusinessCatalogProductItem = {
  product_id: string;
  status: "approved" | "failed";
  product?: BusinessProduct | null;
  error_message?: string | null;
};

export type AdminBulkApproveBusinessCatalogProductResult = {
  requested_limit: number;
  processed_count: number;
  approved_count: number;
  failed_count: number;
  items: AdminBulkApproveBusinessCatalogProductItem[];
};

export type AdminBulkApproveBusinessCatalogProductResponse = {
  result: AdminBulkApproveBusinessCatalogProductResult;
};

export type BusinessCatalogLoadMetrics = {
  product_count: number;
  imports_last_30_days: number;
  largest_import_rows: number;
  images_last_30_days: number;
  failed_imports_last_30_days: number;
};

export type AdminBusinessCatalogMerchantTierCard = {
  merchant: BusinessMerchant;
  assigned_tier: BusinessCatalogTenantTier;
  recommended_tier: BusinessCatalogTenantTier;
  recommendation_reasons: string[];
  metrics: BusinessCatalogLoadMetrics;
  queue_partition: string;
  storage_prefix: string;
  rate_limit_bucket: string;
  hot_account_mode: boolean;
};

export type AdminBusinessCatalogMerchantTierListResponse = {
  merchants: AdminBusinessCatalogMerchantTierCard[];
};

export type AdminBusinessCatalogMerchantTierResponse = {
  merchant: AdminBusinessCatalogMerchantTierCard;
};

export type AdminAssignBusinessCatalogMerchantTierPayload = {
  assigned_tier: BusinessCatalogTenantTier;
  reason: string;
};

export type SimilarSearchClickAnalyticsItem = {
  key: string;
  label: string;
  click_count: number;
};

export type SimilarSearchClickAnalyticsSummary = {
  total_clicks: number;
  redirect_clicks: number;
  local_only_clicks: number;
};

export type SimilarSearchClickAnalyticsResponse = {
  summary: SimilarSearchClickAnalyticsSummary;
  top_products: SimilarSearchClickAnalyticsItem[];
  top_marketplaces: SimilarSearchClickAnalyticsItem[];
  top_cities: SimilarSearchClickAnalyticsItem[];
};

export type BusinessProductImage = {
  image_id: string;
  product_id: string;
  object_key: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  role: BusinessProductImageRole;
  sort_order: number;
  created_at: string;
};

export type BusinessProductImageResponse = {
  image: BusinessProductImage;
};

export type BusinessCatalogImportJob = {
  import_id: string;
  merchant_id: string;
  owner_id: string;
  filename: string;
  status: BusinessCatalogImportStatus;
  total_rows: number;
  accepted_rows: number;
  rejected_rows: number;
  error_summary?: string | null;
  created_at: string;
  completed_at?: string | null;
};

export type BusinessCatalogImportRowError = {
  import_id: string;
  row_number: number;
  field_name: string;
  safe_code: string;
  message: string;
};

export type BusinessCatalogImportResponse = {
  import_job: BusinessCatalogImportJob;
  errors: BusinessCatalogImportRowError[];
};

export type BusinessCatalogImportJobResponse = {
  import_job: BusinessCatalogImportJob;
};

export type BusinessCatalogImportErrorsResponse = {
  errors: BusinessCatalogImportRowError[];
};
