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

export type TryOnWorkflowType = "try_on";

export type TryOnJobStatus =
  | "accepted"
  | "validating_inputs"
  | "generating"
  | "quality_checking"
  | "completed"
  | "failed";

export type TryOnInputMetadata = {
  role: string;
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
      result: TryOnResult;
    }
  | {
      status: "not_ready";
      job_id: string;
      workflow_type: TryOnWorkflowType;
      message: string;
      status_url: string;
    };

export type ApiErrorResponse = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};
