import type {
  ProductCardCreatePayload,
  ProductCardGarmentAnalysisResponse,
  ProductCardJobResponse,
  ProductCardResultResponse,
  TryOnJobCreatedResponse,
  TryOnJobStatusResponse,
  TryOnPreGenerationAnalysisResponse,
  TryOnResultResponse,
  TryOnWearControlSelectionRequest,
  TryOnWearControlSelectionResponse,
} from "@/lib/api/contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class TryOnApiClient extends BaseApiClient {
  public async createTryOnJob(payload: FormData): Promise<TryOnJobCreatedResponse> {
    const response = await fetch(`${this.baseUrl}/api/try-on/jobs`, {
      method: "POST",
      body: payload,
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnJobCreatedResponse>;
  }

  public async continueTryOnGeneration(jobId: string): Promise<TryOnJobCreatedResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${encodeURIComponent(jobId)}/generate`, {
      method: "POST",
      body: new FormData(),
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
}
