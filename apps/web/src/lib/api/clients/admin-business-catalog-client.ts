import type {
  AdminAssignBusinessCatalogMerchantTierPayload,
  AdminBulkApproveBusinessCatalogProductPayload,
  AdminBulkApproveBusinessCatalogProductResponse,
  AdminBulkValidateBusinessCatalogProductCategoryPayload,
  AdminBulkValidateBusinessCatalogProductCategoryResponse,
  AdminBusinessCatalogCredentials,
  AdminBusinessCatalogMerchantTierListResponse,
  AdminBusinessCatalogMerchantTierResponse,
  AdminBusinessCatalogPendingProductsResponse,
  AdminMarketplaceDiscoveryCandidateFilters,
  AdminMarketplaceDiscoveryCandidateListResponse,
  AdminMarketplaceDiscoveryCandidateMutationResponse,
  AdminRejectBusinessCatalogProductPayload,
  AdminRejectMarketplaceDiscoveryCandidatePayload,
  AdminValidateBusinessCatalogProductCategoryPayload,
  BusinessProductResponse,
  SimilarSearchClickAnalyticsResponse,
} from "@/lib/api/business-catalog-contracts";
import { AdminBusinessCatalogDiscoveryApiClient } from "@/lib/api/clients/admin-business-catalog-discovery-client";
import { AdminBusinessCatalogMerchantApiClient } from "@/lib/api/clients/admin-business-catalog-merchant-client";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class AdminBusinessCatalogApiClient extends BaseApiClient {
  private readonly discoveryClient: AdminBusinessCatalogDiscoveryApiClient;
  private readonly merchantClient: AdminBusinessCatalogMerchantApiClient;

  public constructor(baseUrl: string) {
    super(baseUrl);
    this.discoveryClient = new AdminBusinessCatalogDiscoveryApiClient(baseUrl);
    this.merchantClient = new AdminBusinessCatalogMerchantApiClient(baseUrl);
  }

  public async getAdminBusinessCatalogPendingProducts(
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminBusinessCatalogPendingProductsResponse> {
    const response = await fetch(`${this.baseUrl}/api/admin/business-catalog/products/pending`, {
      headers: this.businessCatalogAdminHeaders(credentials),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminBusinessCatalogPendingProductsResponse>;
  }

  public async approveAdminBusinessCatalogProduct(
    productId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<BusinessProductResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/products/${encodeURIComponent(productId)}/approve`,
      {
        method: "POST",
        headers: this.businessCatalogAdminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async rejectAdminBusinessCatalogProduct(
    productId: string,
    payload: AdminRejectBusinessCatalogProductPayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<BusinessProductResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/products/${encodeURIComponent(productId)}/reject`,
      {
        method: "POST",
        headers: {
          ...this.businessCatalogAdminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async archiveAdminBusinessCatalogProduct(
    productId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<BusinessProductResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/products/${encodeURIComponent(productId)}/archive`,
      {
        method: "POST",
        headers: this.businessCatalogAdminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async validateAdminBusinessCatalogProductCategory(
    productId: string,
    payload: AdminValidateBusinessCatalogProductCategoryPayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<BusinessProductResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/products/${encodeURIComponent(productId)}/category-validation`,
      {
        method: "POST",
        headers: {
          ...this.businessCatalogAdminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async runAdminBusinessCatalogProductCategoryValidation(
    productId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<BusinessProductResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/products/${encodeURIComponent(productId)}/category-validation/run`,
      {
        method: "POST",
        headers: this.businessCatalogAdminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async runAdminBusinessCatalogProductCategoryValidationBatch(
    payload: AdminBulkValidateBusinessCatalogProductCategoryPayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminBulkValidateBusinessCatalogProductCategoryResponse> {
    const response = await fetch(`${this.baseUrl}/api/admin/business-catalog/products/category-validation/run-batch`, {
      method: "POST",
      headers: {
        ...this.businessCatalogAdminHeaders(credentials),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminBulkValidateBusinessCatalogProductCategoryResponse>;
  }

  public async approveAdminBusinessCatalogMatchedProductBatch(
    payload: AdminBulkApproveBusinessCatalogProductPayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminBulkApproveBusinessCatalogProductResponse> {
    const response = await fetch(`${this.baseUrl}/api/admin/business-catalog/products/approve-matched-batch`, {
      method: "POST",
      headers: {
        ...this.businessCatalogAdminHeaders(credentials),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminBulkApproveBusinessCatalogProductResponse>;
  }

  public async retryAdminBusinessCatalogProductSearchIndex(
    productId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<BusinessProductResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/products/${encodeURIComponent(productId)}/search-index/retry`,
      {
        method: "POST",
        headers: this.businessCatalogAdminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async getAdminBusinessCatalogMerchantTiers(
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminBusinessCatalogMerchantTierListResponse> {
    return this.merchantClient.getAdminBusinessCatalogMerchantTiers(credentials);
  }

  public async getAdminSimilarSearchAnalytics(
    credentials: AdminBusinessCatalogCredentials,
    limit = 10,
  ): Promise<SimilarSearchClickAnalyticsResponse> {
    return this.merchantClient.getAdminSimilarSearchAnalytics(credentials, limit);
  }

  public async getAdminMarketplaceDiscoveryCandidates(
    credentials: AdminBusinessCatalogCredentials,
    filters: AdminMarketplaceDiscoveryCandidateFilters = {},
  ): Promise<AdminMarketplaceDiscoveryCandidateListResponse> {
    return this.discoveryClient.getAdminMarketplaceDiscoveryCandidates(credentials, filters);
  }

  public async approveAdminMarketplaceDiscoveryCandidate(
    candidateId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminMarketplaceDiscoveryCandidateMutationResponse> {
    return this.discoveryClient.approveAdminMarketplaceDiscoveryCandidate(candidateId, credentials);
  }

  public async rejectAdminMarketplaceDiscoveryCandidate(
    candidateId: string,
    payload: AdminRejectMarketplaceDiscoveryCandidatePayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminMarketplaceDiscoveryCandidateMutationResponse> {
    return this.discoveryClient.rejectAdminMarketplaceDiscoveryCandidate(candidateId, payload, credentials);
  }

  public async archiveAdminMarketplaceDiscoveryCandidate(
    candidateId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminMarketplaceDiscoveryCandidateMutationResponse> {
    return this.discoveryClient.archiveAdminMarketplaceDiscoveryCandidate(candidateId, credentials);
  }

  public async assignAdminBusinessCatalogMerchantTier(
    merchantId: string,
    payload: AdminAssignBusinessCatalogMerchantTierPayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminBusinessCatalogMerchantTierResponse> {
    return this.merchantClient.assignAdminBusinessCatalogMerchantTier(merchantId, payload, credentials);
  }
}
