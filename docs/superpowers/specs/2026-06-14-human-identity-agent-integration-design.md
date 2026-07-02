# Human Identity Agent Enterprise Integration Design

**Date:** 2026-06-14  
**Scope:** First isolated Wave 3 agent integration  
**Status:** Approved design basis

**Staging status:** Deployed on `2026-06-14`; direct Gemini structured and synthetic-image multimodal smoke calls passed.

## 1. Goal

Connect the Human Identity Agent as a mandatory backend-controlled analysis gate in the Try-On workflow.

The agent analyzes only visible preservation constraints. It must never identify a person, infer protected attributes, change workflow state, persist data, call another agent, or decide billing.

## 2. Enterprise Runtime Rules

1. FastAPI and the worker remain the only workflow orchestrators.
2. The Human Identity Agent is invoked only through `AgentInvocationService`.
3. The invocation uses versioned request, prompt, and output contracts.
4. The backend validates the response before any workflow use.
5. The validated analysis is persisted as part of the Try-On job aggregate.
6. Generation cannot start until the required analysis succeeds.
7. Agent or validation failure safely fails the job before generation.
8. Failed analysis is not charged to the user.
9. No direct agent-to-agent calls or A2A contracts are introduced.
10. The invocation ledger stores safe metadata, not raw image bytes or secrets.
11. Approved artifact references are resolved and integrity-checked by the backend; text-only runtimes fail closed instead of producing image analysis from metadata.

## 3. Workflow Position

```text
Upload validation
  -> Store approved human and garment artifacts
  -> Human Identity Agent analysis
  -> Validate structured output
  -> Persist analysis in Try-On job
  -> Backend applies continuation policy
  -> Generation may start
```

This first slice connects only Human Identity Agent. Garment Identity and Material / Texture remain separate subsequent slices.

## 4. Domain Model

The Try-On aggregate receives:

- a typed human identity analysis snapshot;
- the source agent invocation identifier;
- prompt and contract versions;
- analysis completion timestamp;
- backend continuation verdict.

The persisted analysis contains:

- face visibility;
- pose summary;
- visible body regions;
- preservation targets;
- evidence;
- unknowns;
- limitations;
- confidence;
- uncertainty level.

The aggregate does not persist the raw prompt, raw provider response, secret values, or image bytes.

## 5. Backend Continuation Policy

The backend, not the agent, decides whether generation may continue.

Generation is blocked when:

- invocation fails;
- output contract validation fails;
- face is not visible;
- no body region is visible;
- confidence is below the configured minimum;
- uncertainty is high;
- required preservation targets are absent.

The initial enterprise policy is fail-closed. A future policy may return `request_better_input`, but this slice maps blocked analysis to a typed failed Try-On job because the current public job contract has no dedicated input-remediation state.

Thresholds must be backend configuration, not prompt text.

## 6. Invocation Request

The service builds `HumanIdentityRequest` using:

- the approved human photo object key;
- the fixed allow-listed requested checks;
- safe backend facts only.

The request is sent through `AgentInvocationService` with:

- `agent_name`;
- `prompt_version`;
- `contract_version`;
- `trace_id` equal to the Try-On job identifier;
- strict JSON response schema;
- configured timeout;
- configured preferred model.

## 7. Persistence

The Human Identity analysis is persisted through the existing `TryOnJobRepositoryPort`.

Both in-memory and SQL repositories must round-trip the new typed fields. Existing jobs without an analysis remain readable through nullable/default fields.

No separate Human Identity repository is introduced because the analysis belongs to one Try-On job lifecycle. Reusable person-profile or biometric storage is explicitly out of scope.

## 8. Error Handling

Agent failure produces a typed Try-On failure:

- error code: `human_identity_analysis_failed`;
- safe message without provider secrets;
- details containing only job id, stage, and safe failure code;
- zero charged credits;
- no generation invocation.

Backend continuation-policy rejection produces:

- error code: `human_identity_input_not_suitable`;
- safe limitations and failed policy checks;
- zero charged credits;
- no generation invocation.

All failures are logged and persisted. No silent fallback to skipping analysis is allowed.

## 9. Runtime Wiring

`TryOnWorkflowService` receives a dedicated `HumanIdentityAnalysisPort`.

The adapter/use-case service behind this port:

- builds the versioned agent request;
- invokes the canonical agent service;
- validates the typed Human Identity contract;
- applies backend continuation policy;
- returns a typed analysis result or typed safe failure.

The Try-On workflow imports only the dedicated port and domain result. It must not import the ADK agent root.

## 10. Testing

Required tests:

1. Valid Human Identity output is persisted before generation.
2. Generation receives no call when agent invocation fails.
3. Generation receives no call when output validation fails.
4. Generation receives no call when backend continuation policy rejects the analysis.
5. Sensitive or prohibited request fields are rejected before invocation.
6. SQL and in-memory repositories round-trip the analysis.
7. Existing Try-On jobs without analysis remain readable.
8. Invocation metadata is recorded in the canonical audit ledger.
9. Architecture tests prohibit direct Try-On imports of Human Identity agent roots.

## 11. Observability

Record:

- invocation status and validation status;
- prompt and contract versions;
- provider and model;
- latency and safe cost metadata;
- confidence and uncertainty;
- backend continuation verdict;
- safe rejection reason codes.

Do not record raw prompts, unrestricted responses, secrets, or image bytes.

## 12. Exit Criteria

This slice is complete only when:

- Human Identity Agent is mandatory before Try-On generation;
- validated output is durably persisted;
- unsafe or unsuitable analysis blocks generation;
- failure never charges the user;
- all targeted and repository-wide checks pass;
- staging confirms healthy API/worker behavior and persisted invocation audit metadata.
