# FitFabrica Workspace Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the unified `/workspace` experience so it matches the approved workspace design document, preserves the existing backend-connected try-on workflow, upgrades the dashboard/sidebar/page structure into a capability-driven workspace shell, normalizes typography and spacing across all workspace blocks, and ships a verified production deployment for frontend and backend where required.

**Architecture:** Keep the workspace as a thin Next.js client over backend-owned workflow state. Extend the existing typed API boundary with a dedicated workspace state contract and workflow-specific capability flags, then rebuild the dashboard and workspace routes around that state instead of hardcoded cards and fake balances. Preserve the current `try-on` job flow and its typed polling/result pages as the regression baseline, then layer new screens and visual refinements around it without moving business logic into React components.

**Tech Stack:** Next.js App Router, React, TypeScript, Tailwind CSS, typed fetch client, FastAPI, Pydantic, existing portable backend runtime/deploy tooling, Firebase Hosting for web, existing backend deployment flow, browser-based visual QA.

---

## Scope And Baseline

Current verified baseline in this worktree:

- `apps/web/src/app/(workspace)/workspace/page.tsx` is still a mostly static dashboard with hardcoded greeting, credits, cards, and recent activity.
- `apps/web/src/components/navigation/workspace-sidebar.tsx` already provides a unified sidebar, but it does not yet reflect capability-driven visibility or include the `integrations` route expected by the design document.
- `apps/web/src/app/(workspace)/workspace/new-fitting/page.tsx`, `apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx`, `apps/web/src/features/workspace/try-on-workflow.tsx`, and `apps/web/src/features/workspace/try-on-result.tsx` form the only live backend-connected workspace workflow today.
- `apps/web/src/lib/api/client.ts` and `apps/web/src/lib/api/contracts.ts` currently expose only demo-request, sign-in, and try-on endpoints/contracts.
- Most other workspace pages (`history`, `credits`, `similar`, `outfit-builder`, `product-card`, `business-profile`, `style-profile`, `content-package`) are still static mock or placeholder screens.
- The approved source of truth for the workspace UX is `docs/working_area_design.pdf`, which defines a single unified workspace, backend-owned capabilities, business-profile unlocks, optional store integration, and route/CTA expectations.

This plan does not assume hidden frontend-only permissions, mock balances, or decorative routes. Every interaction added in this stage must either:

- connect to an existing backend contract,
- connect to a new typed backend contract introduced in this stage, or
- remain intentionally disabled behind an explicit backend-derived capability/state with honest UI copy.

## Product Rules From The Approved Workspace Design

The implementation must preserve these rules from `docs/working_area_design.pdf`:

- One workspace for all users. No separate personal vs business cabinet.
- Credits gate actions, not user role.
- Product card creation remains available without business profile.
- Business profile unlocks brand/store context, templates, export variants, and business history context.
- Store connection is required only for publish/import/sync actions, not for manual generation/export/download/copy.
- Frontend must render backend-driven capability state such as:
  - `product_card_create`
  - `business_templates`
  - `manual_export`
  - `marketplace_publish`
  - `catalog_import`
  - `catalog_sync`
- Try-on and future workflows remain backend-owned jobs with explicit lifecycle states and structured errors.

## Reuse Versus Replacement

Reuse:

- `apps/web/src/features/workspace/try-on-workflow.tsx` as the live workflow baseline
- `apps/web/src/features/workspace/try-on-result.tsx` as the live result/status baseline
- the existing `WebApiClient` structure in `apps/web/src/lib/api/client.ts`
- the existing workspace route group and sidebar shell
- existing deployment workflow already used for Firebase Hosting and backend deploys

Replace or refactor:

- hardcoded dashboard balances, greetings, quick actions, and recent generations
- route naming mismatch where `/workspace/new-fitting` coexists with the intended `/workspace/try-on`
- static mock workspace pages that do not express loading/error/empty/success states
- typography that still relies on ad hoc local sizing instead of stable semantic workspace classes
- any page logic that guesses business/store availability instead of reading typed backend state

## Target Route Map

The unified workspace should converge to this route map:

- `/workspace`
- `/workspace/try-on`
- `/workspace/try-on/new`
- `/workspace/try-on/result`
- `/workspace/outfit-builder`
- `/workspace/similar`
- `/workspace/product-card`
- `/workspace/content-package`
- `/workspace/history`
- `/workspace/credits`
- `/workspace/style-profile`
- `/workspace/business-profile`
- `/workspace/integrations`

Compatibility notes:

- Keep redirects or compatibility links for `/workspace/new-fitting` until all internal links move to `/workspace/try-on` or `/workspace/try-on/new`.
- Do not remove working try-on result routes while dashboard/sidebar refactors are in progress.

## File Structure

Expected new and changed areas:

- `apps/web/src/lib/api/contracts.ts`
  - Add workspace state, capability, recent job, business profile summary, and integration summary contracts.
- `apps/web/src/lib/api/client.ts`
  - Add workspace bootstrap/state fetch and future route-safe helper methods.
- `apps/web/src/features/workspace/`
  - Split the workspace shell into focused components rather than one large dashboard page.
- `apps/web/src/components/navigation/workspace-sidebar.tsx`
  - Make sidebar capability-aware and route-complete.
- `apps/web/src/app/(workspace)/workspace/page.tsx`
  - Convert to a real dashboard wired to workspace bootstrap state.
- `apps/web/src/app/(workspace)/workspace/integrations/page.tsx`
  - Add the missing integrations route.
- `apps/web/src/app/globals.css`
  - Finalize semantic workspace typography and spacing utilities.
- `src/entrypoints/`
  - Add or extend typed backend workspace endpoints if current backend lacks a unified workspace bootstrap response.
- `tests/`
  - Add regression coverage for backend workspace state contracts and frontend contract assumptions where repo tooling supports it.
- `docs/`
  - Update route and workflow documentation if contracts or deploy runbooks change.

## Task 1: Freeze The Workspace Contract Baseline

**Files:**
- Modify: `docs/working_area_design_extracted.txt` (reference only, do not edit unless re-extracting)
- Modify: `apps/web/src/lib/api/contracts.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Create or modify: backend workspace contract files under `src/entrypoints/` and corresponding Pydantic schemas
- Create: `tests/test_workspace_state_contract.py` or equivalent backend contract tests

- [ ] **Step 1: Define a typed workspace bootstrap contract**

The frontend needs one bootstrap payload instead of many hardcoded fragments. Add contracts shaped like:

```ts
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

export type WorkspaceBootstrapResponse = {
  user: {
    first_name: string | null;
    full_name: string | null;
  };
  credits: {
    balance: number;
    currency: "credits";
    low_balance_threshold: number | null;
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
```

- [ ] **Step 2: Keep backend authority for capability decisions**

Do not compute capability access in React from local heuristics like `if business_profile.exists`. The backend may derive flags from account, credits, business profile, and store connection. Frontend should only render capability-driven UI states.

- [ ] **Step 3: Add a dedicated client method**

```ts
public async getWorkspaceBootstrap(): Promise<WorkspaceBootstrapResponse> {
  const response = await fetch(`${this.baseUrl}/api/workspace/bootstrap`);
  if (!response.ok) {
    throw new Error(await this.errorMessage(response));
  }
  return response.json() as Promise<WorkspaceBootstrapResponse>;
}
```

- [ ] **Step 4: Add contract tests before dashboard wiring**

Backend tests should verify:

- bootstrap response is structurally valid,
- capabilities are explicit strings from an allowed enum,
- manual export can be true without store connection,
- publish/import/sync stay false when no connected store exists.

## Task 2: Create A Real Workspace Shell

**Files:**
- Modify: `apps/web/src/components/navigation/workspace-sidebar.tsx`
- Modify: `apps/web/src/lib/routes/workspace-routes.ts`
- Modify: `apps/web/src/app/(workspace)/workspace/layout.tsx`
- Create: `apps/web/src/features/workspace/workspace-shell.tsx`
- Create: `apps/web/src/features/workspace/workspace-shell-loading.tsx`
- Create: `apps/web/src/features/workspace/workspace-shell-error.tsx`

- [ ] **Step 1: Normalize the route inventory**

Update the route source so the sidebar and dashboard actions point to the approved route structure. Add `integrations` explicitly. Keep backward compatibility redirects for legacy links.

- [ ] **Step 2: Make the sidebar capability-aware**

Examples:

- `Product Card` remains visible for all credit-enabled users.
- `Business Profile` remains visible as setup/management entry.
- `Integrations` becomes visible after business profile exists or stays visible with a setup label, depending on final copy, but publish-only actions must remain disabled without store connection.
- If a route is visible but partially locked, use honest copy like `Требуется профиль бизнеса` or `Подключите магазин для публикации`.

- [ ] **Step 3: Add shell-level loading, error, and empty handling**

The workspace layout should support:

- loading while bootstrap state is fetched,
- retry-able error state if backend bootstrap fails,
- responsive shell layout for sidebar and content,
- no hardcoded user name, credits, or history in the shell.

- [ ] **Step 4: Keep the shell thin**

The shell may fetch and distribute `WorkspaceBootstrapResponse`, but it must not implement credit business logic, billing decisions, or workflow orchestration.

## Task 3: Rebuild The `/workspace` Dashboard From Backend State

**Files:**
- Modify: `apps/web/src/app/(workspace)/workspace/page.tsx`
- Create: `apps/web/src/features/workspace/dashboard/workspace-dashboard.tsx`
- Create: `apps/web/src/features/workspace/dashboard/workspace-quick-actions.tsx`
- Create: `apps/web/src/features/workspace/dashboard/workspace-recent-jobs.tsx`
- Create: `apps/web/src/features/workspace/dashboard/workspace-business-cta.tsx`
- Create: `apps/web/src/features/workspace/dashboard/workspace-credits-card.tsx`

- [ ] **Step 1: Remove all hardcoded dashboard content**

Delete hardcoded greeting, fake credit count, static quick actions, and static recent generations from `page.tsx`.

- [ ] **Step 2: Render the dashboard from workspace bootstrap data**

Dashboard sections should be derived from backend state:

- greeting
- credit summary
- quick actions
- recent jobs/recent generations
- business CTA if no business profile exists
- business-focused summary if business profile exists

- [ ] **Step 3: Support true UI states**

For dashboard cards and lists, explicitly implement:

- loading skeletons
- empty recent jobs state
- backend error with retry
- disabled CTA states when capabilities or credits do not allow the action

- [ ] **Step 4: Match the design document's dashboard logic**

Without business profile:

- show `Зарегистрировать бизнес` CTA,
- show personal/workflow-focused quick actions,
- allow product card creation if capability exists.

With business profile:

- emphasize sales preparation actions,
- show connected channels/store summary,
- surface product/content/business context rather than a purely consumer dashboard.

## Task 4: Preserve And Improve The Existing Try-On Flow

**Files:**
- Modify: `apps/web/src/app/(workspace)/workspace/new-fitting/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/try-on/result/page.tsx`
- Modify: `apps/web/src/features/workspace/try-on-workflow.tsx`
- Modify: `apps/web/src/features/workspace/try-on-result.tsx`
- Modify: relevant backend try-on route/contract tests only if contract expansion is needed

- [ ] **Step 1: Keep current backend integration intact**

The current create-job, status, and result flow is the regression baseline. Any UI or route change must continue to support:

- file validation,
- `POST /api/try-on/jobs`,
- `GET /api/jobs/{job_id}/status`,
- `GET /api/jobs/{job_id}/result`.

- [ ] **Step 2: Align the route naming**

Prefer `/workspace/try-on/new` as the primary entry route. Keep `/workspace/new-fitting` as a redirect or compatibility shim rather than a parallel experience.

- [ ] **Step 3: Upgrade visual polish without changing workflow ownership**

Improve:

- upload cards,
- right-side cost/status panel,
- result action hierarchy,
- typography,
- responsive stacking,
- disabled/pending/error visuals.

Do not move retry/repair/quality decisions into frontend logic.

- [ ] **Step 4: Prepare extensibility for result CTAs**

If the backend does not yet support save/retry/repair/report/export actions, render them as:

- disabled with honest copy,
- or feature-flagged placeholders tied to explicit backend capability/state,

but do not render decorative fake success actions.

## Task 5: Convert Placeholder Workspace Pages Into Honest Product Screens

**Files:**
- Modify: `apps/web/src/app/(workspace)/workspace/outfit-builder/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/similar/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/product-card/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/content-package/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/history/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/credits/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/style-profile/page.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/business-profile/page.tsx`
- Create: `apps/web/src/app/(workspace)/workspace/integrations/page.tsx`

- [ ] **Step 1: Remove decorative mock language**

Each page should clearly express one of these states:

- connected and working,
- backend contract coming soon but intentionally gated,
- requires business profile,
- requires store connection,
- no results yet,
- empty state with next step.

- [ ] **Step 2: Reflect the PDF action model**

Examples:

- `product-card` must remain usable without business profile, but business-template/publish blocks should explain what is unlocked later.
- `credits` must show one shared balance, not separate personal/business wallets.
- `history` should visually support future separation between personal results and business projects while staying honest about current data availability.
- `integrations` must explain that manual export/download/copy works without store connection, while auto-publish/import/sync requires a connected store.

- [ ] **Step 3: Keep pages modular**

Do not write giant route files. Split repeated workspace elements into reusable feature components:

- section headers,
- capability lock panels,
- empty state cards,
- credits summary blocks,
- project/history cards.

## Task 6: Standardize Workspace Typography, Rhythm, And Visual Hierarchy

**Files:**
- Modify: `apps/web/src/app/globals.css`
- Modify: affected workspace pages/components under `apps/web/src/app/(workspace)` and `apps/web/src/features/workspace`

- [ ] **Step 1: Define final semantic workspace type scale**

Ensure there is a stable hierarchy for:

- workspace page hero/title
- workspace section title
- workspace card title
- workspace body text
- workspace support/meta text
- status/badge/label text
- form label/help/error text

Example direction:

```css
.workspace-page-title { font-size: clamp(2.25rem, 3vw, 3.25rem); line-height: 1; }
.workspace-page-lead { font-size: clamp(1.05rem, 1.4vw, 1.2rem); line-height: 1.7; }
.workspace-section-title { font-size: clamp(1.45rem, 2vw, 2rem); line-height: 1.15; }
.workspace-card-title { font-size: clamp(1.1rem, 1.5vw, 1.35rem); line-height: 1.25; }
.workspace-body { font-size: 1rem; line-height: 1.7; }
.workspace-meta { font-size: 0.875rem; line-height: 1.5; }
```

- [ ] **Step 2: Remove ad hoc local text sizes**

Replace scattered local `text-[...]` values for core workspace content with semantic classes wherever the text participates in primary hierarchy.

- [ ] **Step 3: Normalize vertical rhythm**

Use consistent section spacing and card internal spacing so blocks do not visually collapse. A practical target is:

- section-to-section spacing: consistent 40-56px range,
- card internal padding: stable tiered spacing by card size,
- aligned button stacks and action rows across pages.

- [ ] **Step 4: Validate responsive typography**

Manually verify:

- 1440px desktop,
- laptop width,
- tablet,
- mobile widths used by the current app.

Typography must remain clean and premium, not oversized and not cramped.

## Task 7: Add Safe Backend Extensions Only Where Required

**Files:**
- Modify: backend entrypoints/schemas/services only if the frontend needs missing state
- Modify: tests covering runtime dependencies and new workspace endpoints
- Modify: backend docs/runbooks if deploy steps change

- [ ] **Step 1: Prefer additive backend changes**

If the backend lacks a workspace bootstrap endpoint, add one as a thin composition endpoint that aggregates:

- user display info,
- credits balance,
- business profile summary,
- connected store summary,
- capabilities,
- recent jobs summary.

- [ ] **Step 2: Do not move orchestration into this endpoint**

This endpoint is read-only bootstrap state. It must not create jobs, mutate credits, or duplicate workflow rules already owned by dedicated use cases.

- [ ] **Step 3: Preserve portable architecture**

New backend code must respect:

- entrypoints -> use cases -> adapters separation,
- typed DTOs/Pydantic schemas,
- no hidden coupling to frontend-specific fake data,
- no vendor-specific hardcoding if current backend foundation already abstracts it.

## Task 8: Verification Before Claiming Completion

**Files/commands:**
- `apps/web`
- backend root test/lint commands
- browser-based visual QA artifacts if needed

- [ ] **Step 1: Run frontend verification**

At minimum:

```powershell
cd C:\Code\Ai Fitfabrica\apps\web
npm run lint
npm run typecheck
npm run build
```

- [ ] **Step 2: Run backend verification if backend changed**

Use the repo's existing test path, for example:

```powershell
cd C:\Code\Ai Fitfabrica
pytest
```

If the backend scope is large, at least run the targeted tests for new workspace contracts plus any existing runtime dependency tests touched by the changes.

- [ ] **Step 3: Run self-review**

Before finalizing, perform the required self-check from project instructions:

```powershell
cd C:\Code\Ai Fitfabrica
codex /review
```

If `codex /review` is unavailable in this environment, state that explicitly and replace it with a manual code review pass over changed files plus command outputs.

## Task 9: Deploy Frontend And Backend Safely

**Files/commands:**
- Firebase Hosting config in repo root
- backend deploy scripts/runbooks already present in repo
- environment configuration if new API route is added

- [ ] **Step 1: Deploy frontend after green verification**

```powershell
cd C:\Code\Ai Fitfabrica\apps\web
npm run build

cd C:\Code\Ai Fitfabrica
firebase deploy --only hosting
```

- [ ] **Step 2: Deploy backend only if backend changed**

Use the repo's current backend deployment path rather than inventing a new one. Validate:

- environment variables for any new workspace endpoint,
- no broken dependency wiring,
- deployed API base remains aligned with `NEXT_PUBLIC_API_BASE_URL`.

- [ ] **Step 3: Record what actually changed**

If only frontend changed, state that clearly. If backend changed, name the deployed backend surface explicitly, including any new `/api/workspace/bootstrap` endpoint.

## Task 10: Post-Deploy Browser QA And Visual Polish Loop

**Files/tools:**
- local browser plugin / live domain checks
- workspace routes on localhost and live domain

- [ ] **Step 1: Verify local and live workspace routes**

Open and inspect:

- `http://localhost:3000/workspace/`
- `http://localhost:3000/workspace/try-on/new`
- any other changed workspace routes
- live hosted equivalents after deploy

- [ ] **Step 2: Validate visual details against the approved design**

Check:

- hero/dashboard block hierarchy,
- sidebar spacing and active state,
- button alignment,
- card spacing,
- heading sizes,
- empty/loading/error states,
- disabled capability messaging,
- responsive layout.

- [ ] **Step 3: Fix issues and redeploy if necessary**

Do not stop after first deploy if:

- text sizes look off,
- sections collapse vertically,
- lock states are misleading,
- dashboard composition feels visually uneven,
- route names/copy still conflict with the design document.

## Execution Order

Implement in this order to minimize regressions:

1. typed workspace bootstrap contracts
2. backend bootstrap endpoint if missing
3. workspace shell + sidebar refactor
4. dashboard rebuild
5. try-on route normalization and visual polish
6. integrations route and honest placeholder-to-product page conversions
7. typography/rhythm final pass
8. verification
9. deploy
10. post-deploy browser QA and final polish

## Definition Of Done For This Workspace Stage

This stage is complete only when:

- `/workspace` is backend-driven rather than hardcoded,
- sidebar and route map reflect the unified workspace model,
- the existing try-on flow still works end-to-end,
- business profile and store connection states are rendered honestly,
- typography and spacing across workspace screens are normalized and visually clean,
- required verification commands pass,
- frontend is deployed,
- backend is deployed if changed,
- live workspace pages are visually checked after deploy,
- any discovered post-deploy design defects are fixed and redeployed.

## Risks And Guardrails

- Do not break the currently working try-on flow while improving the workspace shell.
- Do not replace backend truth with frontend assumptions about credits, business state, or publishability.
- Do not ship decorative actions that appear functional but have no backend behavior.
- Do not keep route duplication permanently; use compatibility redirects during migration only.
- Do not let typography tuning regress accessibility or responsive readability.
