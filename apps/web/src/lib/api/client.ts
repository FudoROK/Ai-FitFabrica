import type {
  ApiErrorResponse,
  DemoRequestDto,
  SignInDto,
  TryOnJobCreatedResponse,
  TryOnJobStatusResponse,
  TryOnResultResponse
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
