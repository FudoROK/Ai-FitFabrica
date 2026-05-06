import type { DemoRequestDto, SignInDto } from "@/lib/api/contracts";

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
}
