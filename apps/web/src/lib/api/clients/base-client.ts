import type { AdminTaxonomyCredentials } from "@/lib/api/admin-contracts";
import type { AdminBusinessCatalogCredentials } from "@/lib/api/business-catalog-contracts";
import type { ApiErrorResponse } from "@/lib/api/contracts";

export class BaseApiClient {
  public constructor(protected readonly baseUrl: string) {}

  protected adminHeaders(credentials: AdminTaxonomyCredentials): HeadersInit {
    return {
      Authorization: `Bearer ${credentials.adminToken}`,
    };
  }

  protected businessCatalogAdminHeaders(credentials: AdminBusinessCatalogCredentials): HeadersInit {
    return {
      Authorization: `Bearer ${credentials.adminToken}`,
    };
  }

  protected async errorMessage(response: Response): Promise<string> {
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
