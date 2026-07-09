import type {
  BusinessCatalogImportErrorsResponse,
  BusinessCatalogImportJobResponse,
  BusinessCatalogImportResponse,
  BusinessMerchantPayload,
  BusinessMerchantResponse,
  BusinessProductCreatePayload,
  BusinessProductImageResponse,
  BusinessProductListResponse,
  BusinessProductResponse,
} from "@/lib/api/business-catalog-contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class BusinessCatalogApiClient extends BaseApiClient {
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
}
