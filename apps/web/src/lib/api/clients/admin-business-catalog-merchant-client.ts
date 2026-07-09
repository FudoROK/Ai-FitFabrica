import type {
  AdminAssignBusinessCatalogMerchantTierPayload,
  AdminBusinessCatalogCredentials,
  AdminBusinessCatalogMerchantTierListResponse,
  AdminBusinessCatalogMerchantTierResponse,
  SimilarSearchClickAnalyticsResponse,
} from "@/lib/api/business-catalog-contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class AdminBusinessCatalogMerchantApiClient extends BaseApiClient {
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
}
