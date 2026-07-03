import type {
  AdminMergeTaxonomyCandidatePayload,
  AdminRenameAndApproveTaxonomyCandidatePayload,
  AdminRejectTaxonomyCandidatePayload,
  AdminTaxonomyCandidateMutationResponse,
  AdminTaxonomyCandidatesResponse,
  AdminTaxonomyCredentials,
} from "@/lib/api/admin-contracts";
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
  AdminRejectMarketplaceDiscoveryCandidatePayload,
  AdminRejectBusinessCatalogProductPayload,
  AdminValidateBusinessCatalogProductCategoryPayload,
  BusinessCatalogImportErrorsResponse,
  BusinessCatalogImportJobResponse,
  BusinessCatalogImportResponse,
  BusinessMerchantPayload,
  BusinessMerchantResponse,
  BusinessProductCreatePayload,
  BusinessProductImageResponse,
  BusinessProductListResponse,
  BusinessProductResponse,
  SimilarSearchClickAnalyticsResponse,
} from "@/lib/api/business-catalog-contracts";
import type {
  ApiErrorResponse,
  AuthLogoutResponse,
  AuthSessionResponse,
  CreditBalanceResponse,
  CreditLedgerResponse,
  DemoRequestDto,
  GarmentWearControlListResponse,
  NoBillingReadinessResponse,
  ProductCardCreatePayload,
  ProductCardGarmentAnalysisResponse,
  ProductCardJobResponse,
  ProductCardResultResponse,
  SignInDto,
  SimilarSearchClickEventPayload,
  SimilarSearchClickEventResponse,
  SimilarSearchResponse,
  TryOnJobCreatedResponse,
  TryOnJobStatusResponse,
  TryOnPreGenerationAnalysisResponse,
  TryOnResultResponse,
  TryOnWearControlSelectionRequest,
  TryOnWearControlSelectionResponse,
  WorkspaceBootstrapResponse,
  WorkspaceCatalogImportPayload,
  WorkspaceCatalogImportResponse,
  WorkspaceCatalogSyncPayload,
  WorkspaceCatalogSyncResponse,
  WorkspaceCapability,
  WorkspaceCapabilityMatrixResponse,
  WorkspaceBusinessProfilePayload,
  WorkspaceBusinessProfileResponse,
  WorkspaceIntegrationsPayload,
  WorkspaceIntegrationsResponse,
  WorkspaceMarketplacePublishPayload,
  WorkspaceMarketplacePublishResponse,
  WorkspaceOutfitBuilderBriefResponse,
  WorkspaceOutfitBuilderRequestListResponse,
  WorkspaceOutfitBuilderRequestPayload,
  WorkspaceOutfitBuilderRequestResponse,
  WorkspaceOutfitBuilderRequestStatusResponse,
} from "@/lib/api/contracts";

export class WebApiClient {
  public constructor(private readonly baseUrl: string) {}

  public async requestDemo(payload: DemoRequestDto): Promise<Response> {
    return fetch(`${this.baseUrl}/demo-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  public async signIn(payload: SignInDto): Promise<Response> {
    return fetch(`${this.baseUrl}/auth/sign-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  public async getAuthSession(): Promise<AuthSessionResponse> {
    const response = await fetch(`${this.baseUrl}/auth/session`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AuthSessionResponse>;
  }

  public async logout(): Promise<AuthLogoutResponse> {
    const response = await fetch(`${this.baseUrl}/auth/logout`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AuthLogoutResponse>;
  }

  public async getNoBillingReadiness(statusToken: string): Promise<NoBillingReadinessResponse> {
    const response = await fetch(`${this.baseUrl}/ready`, {
      headers: {
        "X-Status-Token": statusToken,
      },
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<NoBillingReadinessResponse>;
  }

  public async createTryOnJob(payload: FormData): Promise<TryOnJobCreatedResponse> {
    const response = await fetch(`${this.baseUrl}/api/try-on/jobs`, {
      method: "POST",
      body: payload
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnJobCreatedResponse>;
  }

  public async continueTryOnGeneration(jobId: string): Promise<TryOnJobCreatedResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${encodeURIComponent(jobId)}/generate`, {
      method: "POST",
      body: new FormData()
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnJobCreatedResponse>;
  }

  public async saveTryOnWearControls(
    jobId: string,
    payload: TryOnWearControlSelectionRequest,
  ): Promise<TryOnWearControlSelectionResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${encodeURIComponent(jobId)}/wear-controls`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnWearControlSelectionResponse>;
  }

  public async getJobStatus(jobId: string): Promise<TryOnJobStatusResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/status`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnJobStatusResponse>;
  }

  public async getJobResult(jobId: string): Promise<TryOnResultResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/result`);

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnResultResponse>;
  }

  public async getTryOnPreGenerationAnalysis(jobId: string): Promise<TryOnPreGenerationAnalysisResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${encodeURIComponent(jobId)}/pre-generation-analysis`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnPreGenerationAnalysisResponse>;
  }

  public async getWorkspaceBootstrap(): Promise<WorkspaceBootstrapResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/bootstrap`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceBootstrapResponse>;
  }

  public async getGarmentWearControls(garmentType: string): Promise<GarmentWearControlListResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/garment-taxonomy/wear-controls?garment_type=${encodeURIComponent(garmentType)}`
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<GarmentWearControlListResponse>;
  }

  public async createProductCardJob(payload: ProductCardCreatePayload): Promise<ProductCardJobResponse> {
    const response = await fetch(`${this.baseUrl}/api/product-cards`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<ProductCardJobResponse>;
  }

  public async getProductCardJob(jobId: string): Promise<ProductCardJobResponse> {
    const response = await fetch(`${this.baseUrl}/api/product-cards/${encodeURIComponent(jobId)}`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<ProductCardJobResponse>;
  }

  public async getProductCardResult(jobId: string): Promise<ProductCardResultResponse> {
    const response = await fetch(`${this.baseUrl}/api/product-cards/${encodeURIComponent(jobId)}/result`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<ProductCardResultResponse>;
  }

  public async getProductCardGarmentAnalysis(jobId: string): Promise<ProductCardGarmentAnalysisResponse> {
    const response = await fetch(`${this.baseUrl}/api/product-cards/${encodeURIComponent(jobId)}/garment-analysis`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<ProductCardGarmentAnalysisResponse>;
  }

  public async saveWorkspaceBusinessProfile(payload: WorkspaceBusinessProfilePayload): Promise<WorkspaceBusinessProfileResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/business-profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceBusinessProfileResponse>;
  }

  public async getWorkspaceBusinessProfile(): Promise<WorkspaceBusinessProfileResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/business-profile`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceBusinessProfileResponse>;
  }

  public async saveWorkspaceIntegrations(payload: WorkspaceIntegrationsPayload): Promise<WorkspaceIntegrationsResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/integrations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceIntegrationsResponse>;
  }

  public async getWorkspaceIntegrations(): Promise<WorkspaceIntegrationsResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/integrations`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceIntegrationsResponse>;
  }

  public async getWorkspaceCapabilities(): Promise<WorkspaceCapabilityMatrixResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/capabilities`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceCapabilityMatrixResponse>;
  }

  public async assertWorkspaceCapability(capability: WorkspaceCapability): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/workspace/capabilities/${capability}/assert`, {
      method: "POST"
    });

    if (response.status === 204) {
      return;
    }

    throw new Error(await this.errorMessage(response));
  }

  public async createWorkspaceMarketplacePublishAction(
    payload: WorkspaceMarketplacePublishPayload,
  ): Promise<WorkspaceMarketplacePublishResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/actions/marketplace-publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceMarketplacePublishResponse>;
  }

  public async createWorkspaceCatalogImportAction(
    payload: WorkspaceCatalogImportPayload,
  ): Promise<WorkspaceCatalogImportResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/actions/catalog-import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceCatalogImportResponse>;
  }

  public async createWorkspaceCatalogSyncAction(
    payload: WorkspaceCatalogSyncPayload,
  ): Promise<WorkspaceCatalogSyncResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/actions/catalog-sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceCatalogSyncResponse>;
  }

  public async getBusinessMerchant(): Promise<BusinessMerchantResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/merchant`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessMerchantResponse>;
  }

  public async saveBusinessMerchant(payload: BusinessMerchantPayload): Promise<BusinessMerchantResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/merchant`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessMerchantResponse>;
  }

  public async listBusinessProducts(): Promise<BusinessProductListResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/products`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductListResponse>;
  }

  public async createBusinessProduct(payload: BusinessProductCreatePayload): Promise<BusinessProductResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/products`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async submitBusinessProduct(productId: string): Promise<BusinessProductResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/products/${encodeURIComponent(productId)}/submit`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductResponse>;
  }

  public async uploadBusinessProductImage(
    productId: string,
    payload: FormData,
  ): Promise<BusinessProductImageResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/products/${encodeURIComponent(productId)}/images`, {
      method: "POST",
      body: payload,
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessProductImageResponse>;
  }

  public async createBusinessCatalogImport(payload: FormData): Promise<BusinessCatalogImportResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/catalog-imports`, {
      method: "POST",
      body: payload,
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessCatalogImportResponse>;
  }

  public async getBusinessCatalogImport(importId: string): Promise<BusinessCatalogImportJobResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/catalog-imports/${encodeURIComponent(importId)}`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessCatalogImportJobResponse>;
  }

  public async getBusinessCatalogImportErrors(importId: string): Promise<BusinessCatalogImportErrorsResponse> {
    const response = await fetch(`${this.baseUrl}/api/business/catalog-imports/${encodeURIComponent(importId)}/errors`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<BusinessCatalogImportErrorsResponse>;
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
    const response = await fetch(`${this.baseUrl}/api/admin/business-catalog/merchants/tiers`, {
      headers: this.businessCatalogAdminHeaders(credentials),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminBusinessCatalogMerchantTierListResponse>;
  }

  public async getAdminSimilarSearchAnalytics(
    credentials: AdminBusinessCatalogCredentials,
    limit = 10,
  ): Promise<SimilarSearchClickAnalyticsResponse> {
    const response = await fetch(`${this.baseUrl}/api/admin/business-catalog/analytics/similar-search?limit=${limit}`, {
      headers: this.businessCatalogAdminHeaders(credentials),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<SimilarSearchClickAnalyticsResponse>;
  }

  public async getAdminMarketplaceDiscoveryCandidates(
    credentials: AdminBusinessCatalogCredentials,
    filters: AdminMarketplaceDiscoveryCandidateFilters = {},
  ): Promise<AdminMarketplaceDiscoveryCandidateListResponse> {
    const params = new URLSearchParams();
    if (filters.status) {
      params.set("status", filters.status);
    }
    if (filters.source_type) {
      params.set("source_type", filters.source_type);
    }
    if (filters.category?.trim()) {
      params.set("category", filters.category.trim());
    }
    if (filters.city?.trim()) {
      params.set("city", filters.city.trim());
    }
    params.set("limit", String(filters.limit ?? 20));
    const query = params.toString();
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/discovery-candidates${query ? `?${query}` : ""}`,
      {
        headers: this.businessCatalogAdminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminMarketplaceDiscoveryCandidateListResponse>;
  }

  public async approveAdminMarketplaceDiscoveryCandidate(
    candidateId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminMarketplaceDiscoveryCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/discovery-candidates/${encodeURIComponent(candidateId)}/approve`,
      {
        method: "POST",
        headers: this.businessCatalogAdminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminMarketplaceDiscoveryCandidateMutationResponse>;
  }

  public async rejectAdminMarketplaceDiscoveryCandidate(
    candidateId: string,
    payload: AdminRejectMarketplaceDiscoveryCandidatePayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminMarketplaceDiscoveryCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/discovery-candidates/${encodeURIComponent(candidateId)}/reject`,
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

    return response.json() as Promise<AdminMarketplaceDiscoveryCandidateMutationResponse>;
  }

  public async archiveAdminMarketplaceDiscoveryCandidate(
    candidateId: string,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminMarketplaceDiscoveryCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/discovery-candidates/${encodeURIComponent(candidateId)}/archive`,
      {
        method: "POST",
        headers: this.businessCatalogAdminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminMarketplaceDiscoveryCandidateMutationResponse>;
  }

  public async assignAdminBusinessCatalogMerchantTier(
    merchantId: string,
    payload: AdminAssignBusinessCatalogMerchantTierPayload,
    credentials: AdminBusinessCatalogCredentials,
  ): Promise<AdminBusinessCatalogMerchantTierResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/business-catalog/merchants/${encodeURIComponent(merchantId)}/tier`,
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

    return response.json() as Promise<AdminBusinessCatalogMerchantTierResponse>;
  }

  public async getWorkspaceOutfitBuilderBrief(): Promise<WorkspaceOutfitBuilderBriefResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/outfit-builder/brief`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceOutfitBuilderBriefResponse>;
  }

  public async createWorkspaceOutfitBuilderRequest(
    payload: WorkspaceOutfitBuilderRequestPayload,
  ): Promise<WorkspaceOutfitBuilderRequestResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/outfit-builder/requests`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceOutfitBuilderRequestResponse>;
  }

  public async getWorkspaceOutfitBuilderRequests(): Promise<WorkspaceOutfitBuilderRequestListResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/outfit-builder/requests`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceOutfitBuilderRequestListResponse>;
  }

  public async getWorkspaceOutfitBuilderRequestStatus(
    requestId: string,
  ): Promise<WorkspaceOutfitBuilderRequestStatusResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/outfit-builder/requests/${requestId}/status`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceOutfitBuilderRequestStatusResponse>;
  }

  public async getCreditBalance(ownerType: string, ownerId: string): Promise<CreditBalanceResponse> {
    const response = await fetch(`${this.baseUrl}/api/credits/${ownerType}/${encodeURIComponent(ownerId)}`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<CreditBalanceResponse>;
  }

  public async getCreditLedger(ownerType: string, ownerId: string, limit = 20): Promise<CreditLedgerResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/credits/${ownerType}/${encodeURIComponent(ownerId)}/ledger?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<CreditLedgerResponse>;
  }

  public async searchSimilarByGarmentPhoto(payload: FormData): Promise<SimilarSearchResponse> {
    const response = await fetch(`${this.baseUrl}/api/similar-search/garment-photo`, {
      method: "POST",
      body: payload,
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<SimilarSearchResponse>;
  }

  public async recordSimilarSearchClick(payload: SimilarSearchClickEventPayload): Promise<SimilarSearchClickEventResponse> {
    const response = await fetch(`${this.baseUrl}/api/similar-search/events/click`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<SimilarSearchClickEventResponse>;
  }

  public async getAdminTaxonomyCandidates(
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidatesResponse> {
    const response = await fetch(`${this.baseUrl}/api/admin/taxonomy/candidates`, {
      headers: this.adminHeaders(credentials),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidatesResponse>;
  }

  public async approveAdminTaxonomyCandidate(
    candidateId: string,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/approve`,
      {
        method: "POST",
        headers: this.adminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }

  public async rejectAdminTaxonomyCandidate(
    candidateId: string,
    payload: AdminRejectTaxonomyCandidatePayload,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/reject`,
      {
        method: "POST",
        headers: {
          ...this.adminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }

  public async mergeAdminTaxonomyCandidate(
    candidateId: string,
    payload: AdminMergeTaxonomyCandidatePayload,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/merge`,
      {
        method: "POST",
        headers: {
          ...this.adminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }

  public async renameAndApproveAdminTaxonomyCandidate(
    candidateId: string,
    payload: AdminRenameAndApproveTaxonomyCandidatePayload,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/rename-and-approve`,
      {
        method: "POST",
        headers: {
          ...this.adminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }

  private adminHeaders(credentials: AdminTaxonomyCredentials): HeadersInit {
    return {
      Authorization: `Bearer ${credentials.adminToken}`,
    };
  }

  private businessCatalogAdminHeaders(credentials: AdminBusinessCatalogCredentials): HeadersInit {
    return {
      Authorization: `Bearer ${credentials.adminToken}`,
    };
  }

  private async errorMessage(response: Response): Promise<string> {
    try {
      const payload: unknown = await response.json();

      if (isApiErrorResponse(payload)) {
        return payload.error.message;
      }
    } catch {
      return "Backend request failed.";
    }

    return "Backend request failed.";
  }
}

function isApiErrorResponse(payload: unknown): payload is ApiErrorResponse {
  if (!isRecord(payload) || !isRecord(payload.error)) {
    return false;
  }

  return (
    typeof payload.error.code === "string" &&
    typeof payload.error.message === "string" &&
    isRecord(payload.error.details)
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
