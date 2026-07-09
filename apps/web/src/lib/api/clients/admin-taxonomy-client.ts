import type {
  AdminMergeTaxonomyCandidatePayload,
  AdminRejectTaxonomyCandidatePayload,
  AdminRenameAndApproveTaxonomyCandidatePayload,
  AdminTaxonomyCandidateMutationResponse,
  AdminTaxonomyCandidatesResponse,
  AdminTaxonomyCredentials,
} from "@/lib/api/admin-contracts";
import { BaseApiClient } from "@/lib/api/clients/base-client";

export class AdminTaxonomyApiClient extends BaseApiClient {
  public async getAdminTaxonomyCandidates(
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidatesResponse> {
    const response = await fetch(`${this.baseUrl}/api/admin/taxonomy/candidates`, {
      headers: this.adminHeaders(credentials),
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidatesResponse>;
  }

  public async approveAdminTaxonomyCandidate(
    candidateId: string,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/approve`,
      {
        method: "POST",
        headers: this.adminHeaders(credentials),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }

  public async rejectAdminTaxonomyCandidate(
    candidateId: string,
    payload: AdminRejectTaxonomyCandidatePayload,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/reject`,
      {
        method: "POST",
        headers: {
          ...this.adminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }

  public async mergeAdminTaxonomyCandidate(
    candidateId: string,
    payload: AdminMergeTaxonomyCandidatePayload,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/merge`,
      {
        method: "POST",
        headers: {
          ...this.adminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }

  public async renameAndApproveAdminTaxonomyCandidate(
    candidateId: string,
    payload: AdminRenameAndApproveTaxonomyCandidatePayload,
    credentials: AdminTaxonomyCredentials,
  ): Promise<AdminTaxonomyCandidateMutationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/admin/taxonomy/candidates/${encodeURIComponent(candidateId)}/rename-and-approve`,
      {
        method: "POST",
        headers: {
          ...this.adminHeaders(credentials),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<AdminTaxonomyCandidateMutationResponse>;
  }
}
