export type TaxonomyCandidateStatus =
  | "pending_review"
  | "approved"
  | "rejected"
  | "merged"
  | "needs_more_examples";

export type AdminTaxonomyCandidate = {
  id: string;
  proposed_code: string;
  proposed_display_name: string;
  proposed_category: string;
  proposed_parent_code?: string | null;
  proposed_controls: string[];
  source_job_ids: string[];
  examples_count: number;
  confidence: number;
  agent_reasoning_summary: string;
  status: TaxonomyCandidateStatus;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  review_reason?: string | null;
  approved_catalog_item_code?: string | null;
  created_at: string;
};

export type AdminTaxonomyCredentials = {
  adminToken: string;
};

export type AdminTaxonomyCandidatesResponse = {
  candidates: AdminTaxonomyCandidate[];
};

export type AdminTaxonomyCandidateMutationResponse = {
  candidate: AdminTaxonomyCandidate;
};

export type AdminRejectTaxonomyCandidatePayload = {
  review_reason: string;
};

export type AdminMergeTaxonomyCandidatePayload = {
  target_catalog_item_code: string;
};

export type AdminRenameAndApproveTaxonomyCandidatePayload = {
  approved_catalog_item_code: string;
  approved_display_name: string;
};
