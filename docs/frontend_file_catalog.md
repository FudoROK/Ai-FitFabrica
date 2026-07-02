# AI FitFabrica Frontend File Catalog

Last updated: `2026-06-13`

This catalog describes the active production frontend in `apps/web`.

## 1. Frontend Root

Main zones:

- `src/app` - route layer
- `src/features` - feature modules
- `src/components` - shared UI
- `src/lib` - API client, routes, content, utilities
- `public/images` - static page and brand assets

## 2. Route Layer

Global:

- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/globals.css`

Public routes:

- `apps/web/src/app/(public)/page.tsx`
- `apps/web/src/app/(public)/for-you/page.tsx`
- `apps/web/src/app/(public)/business/page.tsx`
- `apps/web/src/app/(public)/capabilities/page.tsx`
- `apps/web/src/app/(public)/pricing/page.tsx`
- `apps/web/src/app/(public)/how-it-works/page.tsx`
- `apps/web/src/app/(public)/contacts/page.tsx`
- `apps/web/src/app/(public)/privacy/page.tsx`
- `apps/web/src/app/(public)/sign-in/page.tsx`

Workspace routes:

- `apps/web/src/app/(workspace)/workspace/page.tsx`
- `apps/web/src/app/(workspace)/workspace/new-fitting/page.tsx`
- `apps/web/src/app/(workspace)/workspace/try-on/page.tsx`
- `apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx`
- `apps/web/src/app/(workspace)/workspace/try-on/result/page.tsx`
- `apps/web/src/app/(workspace)/workspace/similar/page.tsx`
- `apps/web/src/app/(workspace)/workspace/similar-search/page.tsx`
- `apps/web/src/app/(workspace)/workspace/product-card/page.tsx`
- `apps/web/src/app/(workspace)/workspace/content-package/page.tsx`
- `apps/web/src/app/(workspace)/workspace/outfit-builder/page.tsx`
- `apps/web/src/app/(workspace)/workspace/history/page.tsx`
- `apps/web/src/app/(workspace)/workspace/credits/page.tsx`
- `apps/web/src/app/(workspace)/workspace/business-profile/page.tsx`
- `apps/web/src/app/(workspace)/workspace/integrations/page.tsx`
- `apps/web/src/app/(workspace)/workspace/projects/page.tsx`
- `apps/web/src/app/(workspace)/workspace/settings/page.tsx`
- `apps/web/src/app/(workspace)/workspace/style-profile/page.tsx`
- `apps/web/src/app/(workspace)/workspace/chat/page.tsx`

## 3. Navigation and Shell

Navigation:

- `apps/web/src/components/navigation/public-header.tsx`
- `apps/web/src/components/navigation/public-footer.tsx`
- `apps/web/src/components/navigation/workspace-sidebar.tsx`

Workspace shell and state handling:

- `apps/web/src/features/workspace/workspace-runtime.tsx`
- `apps/web/src/features/workspace/workspace-shell-loading.tsx`
- `apps/web/src/features/workspace/workspace-shell-error.tsx`
- `apps/web/src/features/workspace/workspace-shell-empty.tsx`
- `apps/web/src/features/workspace/workspace-shell-state.tsx`
- `apps/web/src/features/workspace/workspace-section-primitives.tsx`

These modules are responsible for backend bootstrap, route-safe state handling, and thin-client workspace wiring.

## 4. Workspace Feature Modules

Main workspace feature modules:

- `workspace-content-package-overview.tsx`
- `workspace-product-card-overview.tsx`
- `product-card-workflow.tsx`
- `workspace-locked-production-actions.tsx`
- `workspace-outfit-builder-overview.tsx`
- `workspace-credits-view.tsx`
- `workspace-business-profile-form.tsx`
- `workspace-integrations-form.tsx`
- `workspace-settings-overview.tsx`
- `workspace-capability-summary-panel.tsx`
- `workspace-capability-cta.tsx`
- `use-workspace-capability-verdict.ts`

Expected frontend behavior:

- consume backend bootstrap and capability matrix;
- avoid workflow or billing logic in React;
- render explicit loading, error, empty, success, and disabled states.

## 5. Public Feature Modules

Public forms:

- `apps/web/src/features/public/contact-form.tsx`
- `apps/web/src/features/public/sign-in-form.tsx`

These forms should stay connected to real submit behavior or an explicitly limited non-decorative scope.

## 6. API Layer

Frontend API boundary:

- `apps/web/src/lib/api/config.ts`
- `apps/web/src/lib/api/client.ts`
- `apps/web/src/lib/api/contracts.ts`

This is the canonical frontend boundary for backend communication.

## 7. Content and Route Metadata

Page content metadata:

- `apps/web/src/lib/content/public-pages.ts`
- `apps/web/src/lib/content/workspace-pages.ts`
- `apps/web/src/lib/content/workspace-pages-extra.ts`

Route metadata:

- `apps/web/src/lib/routes/workspace-routes.ts`

## 8. Assets

Current public image groups:

- `apps/web/public/images/home`
- `apps/web/public/images/for-you`
- `apps/web/public/images/business`

Assets should stay organized by page intent rather than accumulate unstructured files at the repository root.

## 9. Frontend Standard

The active frontend standard is:

- thin-client only
- typed API usage
- real routes and working CTA flows
- explicit loading, error, empty, success, and disabled states
- no business logic in React components
- no broken encoding in active screens

## 10. B2B Catalog And Admin Frontend

Last updated: `2026-06-29`

B2B catalog workspace routes:

- `apps/web/src/app/(workspace)/workspace/business-catalog/page.tsx`
- `apps/web/src/app/(workspace)/workspace/business-catalog/new/page.tsx`
- `apps/web/src/app/(workspace)/workspace/business-catalog/import/page.tsx`

B2B catalog feature modules:

- `apps/web/src/features/workspace/business-catalog/business-catalog-page.tsx`
- `apps/web/src/features/workspace/business-catalog/business-product-form.tsx`
- `apps/web/src/features/workspace/business-catalog/business-catalog-import-page.tsx`

Admin routes:

- `apps/web/src/app/(admin)/admin/business-catalog/page.tsx`
- `apps/web/src/app/(admin)/admin/business-accounts/page.tsx`
- `apps/web/src/app/(admin)/admin/taxonomy/page.tsx`

Admin feature modules:

- `apps/web/src/features/admin/business-catalog-review.tsx`
- `apps/web/src/features/admin/business-accounts.tsx`
- `apps/web/src/features/admin/taxonomy-review.tsx`

Typed API contracts:

- `apps/web/src/lib/api/business-catalog-contracts.ts`
- `apps/web/src/lib/api/admin-contracts.ts`
- `apps/web/src/lib/api/client.ts`

User-facing upload guidance:

- CSV import shows visible short limits and expandable detailed upload limits.
- Product photo upload shows visible image requirements and expandable detailed upload limits.
- Backend remains the source of truth for the real limits; frontend only explains them.

Feature flags:

- `NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI`
- `NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI`
- `NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI`
