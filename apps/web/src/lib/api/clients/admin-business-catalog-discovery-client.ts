import type {
  AdminBusinessCatalogCredentials,
  AdminMarketplaceDiscoveryCandidateFilters,
  AdminMarketplaceDiscoveryCandidateListResponse,
  AdminMarketplaceDiscoveryCandidateMutationResponse,
  AdminRejectMarketplaceDiscoveryCandidatePayload,
} from "@/lib/api/business-catalog-contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class AdminBusinessCatalogDiscoveryApiClient extends BaseApiClient {
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
}
