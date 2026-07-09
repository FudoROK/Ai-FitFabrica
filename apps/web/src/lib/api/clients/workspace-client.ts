import type {
  GarmentWearControlListResponse,
  WorkspaceBootstrapResponse,
  WorkspaceBusinessProfilePayload,
  WorkspaceBusinessProfileResponse,
  WorkspaceCatalogImportPayload,
  WorkspaceCatalogImportResponse,
  WorkspaceCatalogSyncPayload,
  WorkspaceCatalogSyncResponse,
  WorkspaceCapability,
  WorkspaceCapabilityMatrixResponse,
  WorkspaceIntegrationsPayload,
  WorkspaceIntegrationsResponse,
  WorkspaceMarketplacePublishPayload,
  WorkspaceMarketplacePublishResponse,
} from "@/lib/api/contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class WorkspaceApiClient extends BaseApiClient {
  public async getWorkspaceBootstrap(): Promise<WorkspaceBootstrapResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/bootstrap`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceBootstrapResponse>;
  }

  public async getGarmentWearControls(garmentType: string): Promise<GarmentWearControlListResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/garment-taxonomy/wear-controls?garment_type=${encodeURIComponent(garmentType)}`,
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<GarmentWearControlListResponse>;
  }

  public async saveWorkspaceBusinessProfile(
    payload: WorkspaceBusinessProfilePayload,
  ): Promise<WorkspaceBusinessProfileResponse> {
    const response = await fetch(`${this.baseUrl}/api/workspace/business-profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
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

  public async saveWorkspaceIntegrations(
    payload: WorkspaceIntegrationsPayload,
  ): Promise<WorkspaceIntegrationsResponse> {
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
      method: "POST",
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
      body: JSON.stringify(payload),
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
      body: JSON.stringify(payload),
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
      body: JSON.stringify(payload),
    });

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<WorkspaceCatalogSyncResponse>;
  }
}
