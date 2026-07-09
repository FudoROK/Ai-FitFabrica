import type {
  CreditBalanceResponse,
  CreditLedgerResponse,
  SimilarSearchClickEventPayload,
  SimilarSearchClickEventResponse,
  SimilarSearchResponse,
  WorkspaceOutfitBuilderBriefResponse,
  WorkspaceOutfitBuilderRequestListResponse,
  WorkspaceOutfitBuilderRequestPayload,
  WorkspaceOutfitBuilderRequestResponse,
  WorkspaceOutfitBuilderRequestStatusResponse,
} from "@/lib/api/contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class WorkspaceCommerceApiClient extends BaseApiClient {
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
      body: JSON.stringify(payload),
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
      `${this.baseUrl}/api/credits/${ownerType}/${encodeURIComponent(ownerId)}/ledger?limit=${limit}`,
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

  public async recordSimilarSearchClick(
    payload: SimilarSearchClickEventPayload,
  ): Promise<SimilarSearchClickEventResponse> {
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
}
