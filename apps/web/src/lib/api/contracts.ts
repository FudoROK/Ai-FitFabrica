export type DemoRequestDto = {
  name: string;
  email: string;
  company?: string;
  message?: string;
};

export type SignInDto = {
  email: string;
  password: string;
};

export type AuthSessionResponse = {
  authenticated: boolean;
  auth_configured: boolean;
  user: null;
};

export type AuthLogoutResponse = {
  ok: boolean;
  authenticated: boolean;
};

export type TryOnWorkflowType = "try_on";

export type TryOnJobStatus =
  | "accepted"
  | "validating_inputs"
  | "analyzing_human"
  | "analysis_ready"
  | "generating"
  | "quality_checking"
  | "repairing"
  | "completed"
  | "failed";

export type TryOnInputMetadata = {
  role:
    | "human_photo"
    | "garment_photo"
    | "upper_garment_photo"
    | "lower_garment_photo"
    | "outerwear_garment_photo"
    | "full_body_garment_photo";
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
};

export type TryOnStatusEvent = {
  status: TryOnJobStatus;
  stage: string;
  message: string;
  occurred_at: string;
};

export type TryOnCostEvent = {
  event_type: string;
  estimated_units: number;
  charge_status: "not_charged";
  charged_credits: number;
  occurred_at: string;
};

export type TryOnQualityCheck = {
  name: string;
  status: "passed" | "warning" | "failed";
  confidence: number;
  message: string;
};

export type TryOnQualityReport = {
  verdict: "pass" | "repair_recommended" | "reject";
  confidence: number;
  checks: TryOnQualityCheck[];
  limitations: string[];
};

export type TryOnResult = {
  job_id: string;
  workflow_type: TryOnWorkflowType;
  result_image: {
    kind: "sandbox_placeholder";
    url: string;
    alt: string;
  };
  quality_report: TryOnQualityReport;
  stylist_note: string;
  input_metadata: TryOnInputMetadata[];
  completed_at: string;
};

export type TryOnJobCreatedResponse = {
  job_id: string;
  workflow_type: TryOnWorkflowType;
  status: TryOnJobStatus;
  input_metadata: TryOnInputMetadata[];
  status_url: string;
  result_url: string;
};

export type TryOnJobStatusResponse = {
  job_id: string;
  workflow_type: TryOnWorkflowType;
  status: TryOnJobStatus;
  status_history: TryOnStatusEvent[];
  cost_events: TryOnCostEvent[];
};

export type TryOnResultResponse =
  | {
      status: "completed";
      job_id: string;
      workflow_type: TryOnWorkflowType;
      result: TryOnResult;
    }
  | {
      status: "not_ready";
      job_id: string;
      workflow_type: TryOnWorkflowType;
      current_status: TryOnJobStatus;
      status_url: string;
    };

export type ApiErrorResponse = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export type GarmentWearControlRiskLevel = "low" | "medium" | "high";

export type GarmentWearControlResponse = {
  control_code: string;
  display_name: string;
  description: string | null;
  instruction_template: string;
  risk_level: GarmentWearControlRiskLevel;
  default_for_auto: boolean;
};

export type GarmentWearControlListResponse = {
  garment_type: string;
  taxonomy_item_code: string | null;
  controls: GarmentWearControlResponse[];
  created_candidate: boolean;
};

export type TryOnGarmentSlotWearControlOptions = {
  slot_role: Exclude<TryOnInputMetadata["role"], "human_photo">;
  garment_type: string;
  taxonomy_item_code: string | null;
  selected_control_code: string;
  controls: GarmentWearControlResponse[];
};

export type TryOnPreGenerationAnalysisResponse = {
  job_id: string;
  workflow_type: TryOnWorkflowType;
  status: "analysis_ready";
  slots: TryOnGarmentSlotWearControlOptions[];
  generate_url: string;
};

export type TryOnWearControlSelectionPayload = {
  slot_role: Exclude<TryOnInputMetadata["role"], "human_photo">;
  selected_control_code: string;
};

export type TryOnWearControlSelectionRequest = {
  selections: TryOnWearControlSelectionPayload[];
};

export type TryOnWearControlSelectionResponse = {
  job_id: string;
  status: "analysis_ready";
  selections: Array<{
    slot_role: string;
    garment_type: string;
    requested_control_code: string;
    resolved_control_code: string;
    display_name: string;
    instruction_template: string;
    risk_level: GarmentWearControlRiskLevel;
    resolved_by: string;
  }>;
};

export type BillingOwnerType = "person" | "business";

export type CreditBalanceResponse = {
  owner_id: string;
  owner_type: BillingOwnerType;
  available_credits: number;
  reserved_credits: number;
};

export type CreditLedgerEvent = {
  event_id: string;
  owner_id: string;
  owner_type: BillingOwnerType;
  event_type: "charge" | "refund" | "adjustment" | "grant";
  credits_delta: number;
  balance_after_event: number;
  workflow_type?: string | null;
  workflow_reference?: string | null;
  stage_name?: string | null;
  charge_policy?: string | null;
  created_at?: string;
};

export type CreditLedgerResponse = {
  owner_id: string;
  owner_type: BillingOwnerType;
  events: CreditLedgerEvent[];
};

export type SimilarSearchResult = {
  product_id: string;
  title: string;
  similarity_score: number;
  price_amount: number;
  currency: string;
  marketplace: string;
  is_cheaper_alternative: boolean;
  explanation: string;
  location_match: string;
  country_code: string | null;
  city: string | null;
  delivery_regions: string[];
  image_url: string | null;
  offer_url: string | null;
};

export type SimilarSearchResponse = {
  results: SimilarSearchResult[];
};

export type SimilarSearchClickEventPayload = {
  product_id: string;
  title: string;
  marketplace: string;
  offer_url: string;
  image_url: string | null;
  user_country_code: string | null;
  user_city: string | null;
};

export type SimilarSearchClickEventResponse = {
  event_id: string;
  redirect_url: string | null;
  redirect_allowed: boolean;
};

export type WorkspaceCapability =
  | "try_on_create"
  | "outfit_builder_create"
  | "similar_search_create"
  | "product_card_create"
  | "business_profile_manage"
  | "business_templates"
  | "manual_export"
  | "marketplace_publish"
  | "catalog_import"
  | "catalog_sync";

export type WorkspaceCreditOwnerSummary = {
  owner_id: string;
  owner_type: BillingOwnerType;
};

export type WorkspaceQuickAction = {
  id: string;
  label: string;
  description: string;
  href: string;
  capability: WorkspaceCapability | null;
  enabled: boolean;
  disabled_reason: string | null;
};

export type WorkspaceRecentJobSummary = {
  job_id: string;
  workflow_type: string;
  title: string;
  status: string;
  href: string;
  updated_at: string;
  summary: string | null;
};

export type WorkspaceBootstrapResponse = {
  user: {
    first_name: string | null;
    full_name: string | null;
  };
  credit_owner: WorkspaceCreditOwnerSummary;
  credits: {
    balance: number;
    currency: "credits";
    low_balance_threshold: number | null;
    billing_enabled: boolean;
  };
  workflow_costs: {
    product_card: number;
  };
  business_profile: {
    exists: boolean;
    display_name: string | null;
    channels: string[];
  };
  integrations: {
    has_connected_store: boolean;
    connected_channels: string[];
  };
  capabilities: WorkspaceCapability[];
  quick_actions: WorkspaceQuickAction[];
  recent_jobs: WorkspaceRecentJobSummary[];
};

export type ProductCardSourceFilePayload = {
  filename: string;
  content_type: string;
  payload_base64: string;
};

export type ProductCardCreatePayload = {
  title_hint: string;
  category: string;
  target_channel: string;
  brand_tone: string;
  source_files: ProductCardSourceFilePayload[];
};

export type ProductCardJobResponse = {
  job_id: string;
  status: string;
  category: string;
  target_channel: string;
  brand_tone: string;
  title_hint?: string | null;
  asset_keys: string[];
  created_at: string;
  updated_at: string;
};

export type ProductCardResultResponse = {
  version_id: string;
  job_id: string;
  title: string;
  description: string;
  bullet_points: string[];
  attributes: Record<string, string>;
  created_at: string;
};

export type ProductCardGarmentAnalysisResponse = {
  job_id: string;
  invocation_id: string;
  prompt_version: string;
  contract_version: string;
  garment_type: string;
  dominant_color: string;
  secondary_colors: string[];
  silhouette_summary: string;
  preserved_details: string[];
  confidence: number;
  limitations: string[];
  visual_details: Array<{
    detail_type: string;
    description: string;
    confidence: number;
  }>;
  evidence: Array<{
    source_type: string;
    source_ref: string;
    observation: string;
    confidence: number;
  }>;
  uncertainty_level: string;
  unknowns: string[];
  completed_at: string;
};

export type WorkspaceBusinessProfilePayload = {
  display_name: string;
  channels: string[];
};

export type WorkspaceBusinessProfileResponse = {
  owner_id: string;
  display_name: string;
  channels: string[];
  created_at?: string | null;
  updated_at?: string | null;
};

export type WorkspaceIntegrationsPayload = {
  connected_channels: string[];
  has_connected_store: boolean;
};

export type WorkspaceIntegrationsResponse = {
  owner_id: string;
  connected_channels: string[];
  has_connected_store: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type WorkspaceCapabilityState = {
  capability: WorkspaceCapability;
  enabled: boolean;
  disabled_reason: string | null;
};

export type WorkspaceCapabilityMatrixResponse = {
  business_profile: {
    exists: boolean;
    display_name: string | null;
    channels: string[];
  };
  integrations: {
    has_connected_store: boolean;
    connected_channels: string[];
  };
  capability_states: WorkspaceCapabilityState[];
  enabled_capabilities: WorkspaceCapability[];
};

export type WorkspaceMarketplacePublishPayload = {
  target_channel: string;
  product_card_version_id: string;
  content_package_version_id?: string | null;
};

export type WorkspaceMarketplacePublishResponse = {
  action: "marketplace_publish";
  status: "accepted";
  target_channel: string;
  product_card_version_id: string;
  content_package_version_id?: string | null;
  message: string;
};

export type WorkspaceCatalogImportPayload = {
  target_channel: string;
  catalog_source: string;
};

export type WorkspaceCatalogImportResponse = {
  action: "catalog_import";
  status: "accepted";
  target_channel: string;
  catalog_source: string;
  message: string;
};

export type WorkspaceCatalogSyncPayload = {
  target_channel: string;
  sync_scope: string;
};

export type WorkspaceCatalogSyncResponse = {
  action: "catalog_sync";
  status: "accepted";
  target_channel: string;
  sync_scope: string;
  message: string;
};

export type WorkspaceOutfitBuilderBriefResponse = {
  workflow: "outfit_builder";
  status: "active";
  hero_title: string;
  hero_description: string;
  input_sections: string[];
  result_sections: string[];
  readiness_note: string;
};

export type WorkspaceOutfitBuilderRequestPayload = {
  occasion: string;
  budget?: string | null;
  base_item?: string | null;
};

export type WorkspaceOutfitBuilderRequestResponse = {
  request_id: string;
  workflow: "outfit_builder";
  status: "accepted" | "completed";
  occasion: string;
  budget?: string | null;
  base_item?: string | null;
  message: string;
  status_url: string;
  created_at?: string | null;
};

export type WorkspaceOutfitBuilderRequestListResponse = {
  workflow: "outfit_builder";
  requests: WorkspaceOutfitBuilderRequestResponse[];
};

export type WorkspaceOutfitBuilderRequestStatusResponse = {
  request_id: string;
  workflow: "outfit_builder";
  status: "completed";
  status_history: Array<{
    status: "accepted" | "completed";
    message: string;
    occurred_at: string;
  }>;
  result_summary: {
    headline: string;
    summary_lines: string[];
  };
};
