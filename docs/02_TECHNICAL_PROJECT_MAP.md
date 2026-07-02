# AI FitFabrica - Technical Project Map

Дата актуализации: 2026-06-17

## 1. Общее дерево проекта

```text
AI FitFabrica
├── alembic/                 # SQL migrations
├── apps/web/                # Next.js frontend
├── deploy/                  # deploy/support artifacts
├── docs/                    # canonical docs + runbooks + reports
├── output/                  # generated reports, PDFs, acceptance outputs
├── scripts/                 # local/devops/reporting scripts
├── src/                     # backend application
├── test-assets/             # local acceptance/evaluation assets
├── tests/                   # backend/frontend/architecture tests
└── tmp/                     # temporary local files
```

## 2. Backend source tree

```text
src/
├── adapters/
├── adk_agents/
├── costs/
├── domain/
├── entrypoints/
├── identity_core/
├── llm/
├── runtime_agents/
├── services/
├── use_cases/
├── utils/
├── settings*.py
├── main.py
└── worker.py
```

### `src/domain/`

Чистые domain models и contracts. Этот слой не должен знать о FastAPI, SQLAlchemy, Google SDK, object storage SDK или frontend.

Ключевые файлы:

- `agent_runtime.py` - provider-neutral request/result/envelope/record для agent invocation.
- `image_agent_contracts.py` - shared image-agent safety/evidence/uncertainty models.
- `try_on.py` - Try-On job/status/cost/result domain.
- `try_on_human_identity.py` - persisted Human Identity analysis snapshot.
- `try_on_analysis.py` - Garment/Material analysis bundle domain.
- `try_on_instruction.py` - Try-On instruction domain.
- `product_card.py` - Product Card jobs, drafts, garment analysis.
- `workspace.py`, `workspace_state.py` - workspace bootstrap/capabilities state.
- `provider_ports.py` - provider-neutral interfaces.
- `billing.py` - credits/account/ledger domain.

### `src/use_cases/`

Application orchestration. Здесь backend решает, какой workflow выполнить, какие ports вызвать и когда списывать credits. Этот слой не должен импортировать Google/Gemini SDK напрямую.

Ключевые папки:

- `agents/` - canonical `AgentInvocationService` и ports.
- `try_on/` - Try-On workflow orchestration, upload validation, analysis bundle, policies, execution.
- `product_card/` - Product Card workflow and ports.
- `content_package/` - Content Package workflow.
- `pricing/` - Pricing workflow.
- `similar_search/` - Similar/Cheaper search workflow.
- `workspace/` - workspace bootstrap, capabilities, profile/integration services.
- `billing/` - backend-owned credits policy and service.

Ключевые Try-On файлы:

- `workflow_service.py` - facade for Try-On workflow.
- `workflow_execution.py` - actual workflow stage execution.
- `workflow_upload_validation.py` - upload validation.
- `analysis_bundle_service.py` - mandatory Human/Garment/Material analysis bundle.
- `human_identity_policy.py` - backend fail-closed continuation policy.
- `instruction_errors.py`, `analysis_errors.py`, `human_identity_errors.py` - typed workflow failures.

### `src/adapters/`

Adapters implement external infrastructure and provider integrations behind ports.

Ключевые папки:

- `agents/` - adapters from backend workflows to `AgentInvocationService`.
- `database/sql/` - SQLAlchemy models/repositories.
- `database/firestore/` - retained support/legacy contours, not target for new product workflows.
- `try_on/` - Try-On generation/storage adapters.
- `product_card/` - Product Card generation/storage adapters.
- `workspace/` - workspace persistence adapters.
- `ai/` - provider-facing AI helpers where present.

Important agent adapters:

- `human_identity_analysis.py` - Human Identity production adapter.
- `try_on_garment_identity_analysis.py` - Try-On Garment Identity adapter.
- `try_on_material_texture_analysis.py` - Material / Texture adapter.
- `try_on_instruction.py` - Try-On Instruction adapter.
- `garment_identity_analysis.py` - Product Card Garment Identity adapter.
- `product_card_generation.py` - Product Card Agent generation adapter.
- `adk_agent_gateway.py` - gateway from `AgentInvocationService` to provider runtime.
- `object_storage_artifact_resolver.py` - safe artifact resolution for multimodal invocations.

### `src/adk_agents/`

Agent role packages. Agents define prompts/contracts/deploy config, but do not own orchestration or persistence.

Each agent folder normally contains:

- `contracts.py` - strict Pydantic request/output contract.
- `prompt_config.py` - prompt/instruction, prompt version, contract version.
- `deploy_config.py` - provider/deploy defaults.
- `agent.py` - ADK/root agent wrapper.

Current agent packages:

- `orchestrator_agent`
- `user_profile_agent`
- `business_profile_agent`
- `human_identity_agent`
- `garment_identity_agent`
- `material_texture_agent`
- `try_on_agent`
- `product_card_agent`
- `fashion_stylist_agent`
- `marketplace_agent`
- `trend_agent`
- `pricing_agent`
- `quality_verifier_agent`
- `repair_agent`
- `cost_credits_agent`

### `src/llm/`

Provider runtime and structured LLM abstractions.

Ключевые файлы/папки:

- `provider_runtime.py` - provider runtime assembly.
- `provider_routing.py` - routing layer for provider selection.
- `providers/gemini_structured_provider.py` - Gemini structured provider through Google Gen AI SDK.
- `providers/gemini_structured_client.py` - Google Gen AI SDK client helpers.
- `providers/fake_provider.py` - deterministic/test provider.
- `vertex/` - Vertex parser/invocation compatibility helpers.
- `tasks/`, `profiles/` - task/profile registry layers.

Rule: product workflow code should not import provider SDKs from here directly.

### `src/costs/`

Workflow economics and pricing contour.

- `provider_price_config.py` - versioned provider/model cost config.
- `workflow_cost_estimator.py` - estimates provider cost, internal cost, credits, revenue and margin.
- `credits_pricing_policy.py` - credits recommendation policy.

### `src/entrypoints/`

FastAPI routes and runtime dependency builders.

Ключевые route modules:

- `http_routes.py` - route composition.
- `try_on_routes.py` or Try-On route module where present.
- `product_card_routes.py`
- `workspace_routes.py`
- `workspace_capability_routes.py`
- `workspace_profile_routes.py`
- `workspace_integration_routes.py`
- `credits_routes.py`
- `status_routes.py`

Ключевые runtime modules:

- `runtime_dependencies.py`
- `runtime_dependency_builders.py`
- `runtime_dependency_cache.py`
- `runtime_dependency_contracts.py`
- `runtime_dependency_foundation_builders.py`
- `runtime_dependency_workflow_builders.py`
- `runtime_dependency_product_card_builder.py`

Rule: routes validate DTOs and call use cases. They do not execute business logic inline.

### `src/services/`

Shared technical services not tied to one workflow.

Examples:

- `runtime/feature_flags.py` - runtime feature flags.
- `rate_limit/` - rate limiting.
- `crm/` - CRM support contour.
- `context/`, `dialog/` - older/support contours where present.

### `src/identity_core/`

Portable identity and profile repository/runtime contour.

### `src/runtime_agents/`

Runtime-owned dialog/reply task packages. This is separate from product workflow agents in `src/adk_agents`.

### `src/settings*.py`

Settings are split into focused modules:

- `settings.py` - compatibility/loading entry.
- `settings_model.py` - root settings model.
- `settings_model_platform.py` - platform/runtime settings.
- `settings_model_providers.py` - provider settings.
- `settings_model_try_on.py` - Try-On settings.
- `settings_runtime.py` - runtime helpers.

### `src/main.py`

FastAPI application entrypoint.

### `src/worker.py`

Portable worker process entrypoint for queued workflow execution.

## 3. Frontend tree

```text
apps/web/src/
├── app/
├── components/
├── features/
├── lib/
└── types/
```

### `apps/web/src/app/`

Next.js routes/layouts.

Important route groups:

- `(public)/` - public marketing pages.
- `(workspace)/workspace/` - private workspace routes.
- `layout.tsx` - root layout.
- `globals.css` - global Tailwind/design system styles.

Workspace routes include:

- `/workspace`
- `/workspace/product-card`
- `/workspace/credits`
- `/workspace/business-profile`
- `/workspace/settings`
- `/workspace/integrations`
- `/workspace/try-on`

### `apps/web/src/features/`

Feature modules. Business logic should remain backend-owned.

Important modules:

- `workspace/product-card-workflow.tsx` - Product Card UI workflow.
- `workspace/try-on-workflow.tsx` - Try-On UI workflow.
- `workspace/workspace-runtime.tsx` - workspace data bootstrap.
- `workspace/workspace-capability-cta.tsx` - unified capability-aware CTA.
- `workspace/workspace-credits-view.tsx` - credits view.
- `public/` - public page feature components.

### `apps/web/src/lib/`

Typed frontend helpers:

- `api/client.ts` - typed API client.
- `api/contracts.ts` - frontend API contracts/types.
- `api/config.ts` - API base configuration.
- `routes/` - route definitions.
- `content/` - static page content.

### `apps/web/src/components/`

Reusable UI/navigation components:

- `navigation/public-header.tsx`
- `navigation/public-footer.tsx`
- `navigation/workspace-sidebar.tsx`
- `site/`
- `ui/`

## 4. Database migrations

`alembic/versions/` contains SQL migrations.

Important recent migrations:

- `20260614_000011_agent_invocation_ledger.py`
- `20260614_000012_try_on_human_identity_analysis.py`
- `20260615_000013_product_card_category.py`
- `20260615_000014_product_card_garment_analysis.py`
- `20260615_000015_try_on_analysis_bundle.py`
- `20260615_000016_try_on_instruction.py`

## 5. Scripts

Important scripts:

- `scripts/check_architecture.py` - architecture guardrails.
- `scripts/report_workflow_costs.py` - offline cost report.
- `scripts/deploy_portable_runtime.sh` - remote runtime deploy.
- `scripts/bootstrap_portable_host.sh` - VM/bootstrap support.
- `scripts/platform_foundation_smoke.py` - runtime smoke.
- `scripts/try_on_storage_smoke.py` - storage smoke.
- `scripts/run_tests.sh` - test helper.

## 6. Tests

`tests/` includes:

- workflow tests;
- SQL repository tests;
- route tests;
- frontend route/component tests;
- architecture guardrails;
- agent contract/runtime tests;
- cost/pricing tests;
- acceptance support stubs.

Important architecture tests:

- `tests/architecture/test_agent_runtime_guardrails.py`
- `tests/architecture/test_fitfabrica_agent_guardrails.py`
- `tests/architecture/test_product_card_guardrails.py`
- `tests/architecture/test_try_on_rebase_guardrails.py`
- `tests/architecture/test_billing_guardrails.py`

## 7. Documentation tree

```text
docs/
├── 00_PROJECT_MASTER_PLAN.md
├── 01_ACTION_LOG_CHECKLIST.md
├── 02_TECHNICAL_PROJECT_MAP.md
├── 03_AGENT_SYSTEM_GUIDE.md
├── 04_OWNER_REMAINING_WORK.md
├── costs/
├── reports/
├── runbooks/
├── superpowers/
└── archive/
```

## 8. Where to change things

- Change agent prompt: `src/adk_agents/<agent>/prompt_config.py`
- Change agent schema: `src/adk_agents/<agent>/contracts.py`
- Change backend agent invocation: `src/adapters/agents/*` and `src/use_cases/agents/*`
- Change workflow orchestration: `src/use_cases/<workflow>/`
- Change API route: `src/entrypoints/*_routes.py`
- Change frontend API typing: `apps/web/src/lib/api/contracts.ts`
- Change frontend page/action: `apps/web/src/app/...` and `apps/web/src/features/...`
- Change credits policy: `src/use_cases/billing/` for live billing, `src/costs/` for estimates only
- Change investor economics docs: `docs/costs/*` and `output/pdf/*`

## 9. Things to avoid

- Do not put provider prices in workflow code.
- Do not call AI providers from frontend.
- Do not let agents write to DB or calculate credits.
- Do not use hidden marketplace scraping.
- Do not treat historical `docs/superpowers/plans/*` as the current truth without checking canonical docs.

## 10. 2026-06-29 B2B Catalog Reliability Status

The B2B product catalog now has a backend-owned reliability foundation before marketplace/Instagram search is enabled.

Active backend contours:

- Domain: `src/domain/business_catalog.py`
- Use cases: `src/use_cases/business_catalog/`
- SQL models/repository: `src/adapters/database/sql/business_catalog_models.py`, `business_catalog_repositories.py`, `business_catalog_serialization.py`
- Business API: `src/entrypoints/business_catalog_routes.py`
- Admin API: `src/entrypoints/admin_business_catalog_routes.py`
- Migration: `alembic/versions/20260628_000021_business_catalog.py`

Implemented reliability guardrails:

- Search projection only emits `active` + `approved` products with a matching offer.
- Tenant tier policy supports `standard` and `large`.
- Backend recommends tier from workload metrics, but routing changes only after admin assignment.
- Admin route/page exists for business account tier review.
- Idempotency is supported for CSV import, product image upload, and submit-to-review through `Idempotency-Key`.
- Controlled failure injection covers object storage failure, metadata failure after storage, and import row-error persistence failure.
- Backpressure limits are enforced before heavy work: standard CSV `1,000 rows / 5 MB`, large CSV `25,000 rows / 50 MB`, standard `10` images per product, large `30`.

Frontend surfaces:

- Workspace catalog: `/workspace/business-catalog`
- Product creation: `/workspace/business-catalog/new`
- CSV import: `/workspace/business-catalog/import`
- Admin product review: `/admin/business-catalog`
- Admin business account tier review: `/admin/business-accounts`

Still not enabled:

- Marketplace/Instagram external search connectors.
- Automatic tier promotion/demotion.
- Hourly import limits and concurrent import limits; these wait for real queue/worker integration.
- Production chaos drills; only deterministic local failure-injection tests are enabled.

## 11. 2026-06-29 Location-First Marketplace Search Foundation

Similar/Cheaper Search now has a backend-owned foundation for approved marketplace/catalog sources.

Active contours:

- Source contracts: `src/domain/marketplace_search.py`
- Location ranking: `src/use_cases/similar_search/location_ranking.py`
- Similar Search ranking: `src/use_cases/similar_search/ranking.py`
- Local catalog projection: `src/use_cases/business_catalog/search_projection.py`

Allowed future connector source types:

- `local_catalog`
- `partner_feed`
- `official_api`
- `seller_connected_store`
- `admin_verified_link`
- `instagram_business`

Ranking priority:

1. Same user city.
2. Same user country and delivery to user city.
3. Same user country.
4. Delivery available to user city.
5. Remote offer.
6. Price/budget fit, similarity, availability, and source trust score.

Still not enabled:

- Hidden scraping.
- Live Kaspi/Wildberries/Instagram API calls.
- Browser automation against marketplace pages.
- Direct publishing to seller marketplace accounts.
