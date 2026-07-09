import type {
  AuthLogoutResponse,
  AuthSessionResponse,
  DemoRequestDto,
  NoBillingReadinessResponse,
  SignInDto,
} from "@/lib/api/contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class PublicApiClient extends BaseApiClient {
  public async requestDemo(payload: DemoRequestDto): Promise<Response> {
    return fetch(`${this.baseUrl}/demo-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  public async signIn(payload: SignInDto): Promise<Response> {
    return fetch(`${this.baseUrl}/auth/sign-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
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
}
