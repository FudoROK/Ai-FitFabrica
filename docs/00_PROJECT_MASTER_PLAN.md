# AI FitFabrica - Master Implementation Plan

Дата актуализации: 2026-06-17

## 1. Суть проекта

AI FitFabrica - backend-first fashion-commerce платформа с агентными workflow.

Продукт не является универсальным AI image generator. Главный вопрос проекта:

> Как AI помогает человеку или бизнесу принимать лучшие решения по одежде, карточкам товаров, визуальному контенту, поиску похожих товаров и pricing?

Основная схема:

```text
Web / Mobile thin client
-> FastAPI backend
-> backend workflow / use case
-> AgentInvocationService / provider-neutral ports
-> AI agents / generation providers / search connectors
-> Quality gates
-> PostgreSQL + object storage + vector/search layers
-> credits ledger
-> user-facing result
```

## 2. Архитектурные принципы

- Backend управляет workflow, persistence, billing, retry, repair, quality gates и credits.
- Frontend является тонким клиентом: upload, submit DTO, status polling, result rendering.
- Агенты возвращают structured JSON; они не управляют БД, credits, orchestration или бизнес-решениями.
- Продуктовые workflows не импортируют Google/Gemini/ADK SDK напрямую.
- Provider replacement должен выполняться через adapters/config, а не через переписывание бизнес-логики.
- Credits не являются LLM tokens. Это внутренняя продуктовая валюта.
- Некачественные входные данные должны блокироваться до дорогой генерации.

## 3. Текущий production baseline

Backend:

- FastAPI runtime.
- PostgreSQL как source of truth для jobs, profiles, billing, product data и workflow state.
- Redis для queue/runtime coordination.
- S3-compatible object storage / MinIO contour для media/artifacts.
- Qdrant/vector foundation присутствует как portable layer.
- Agent invocation audit ledger сохраняет safe metadata без raw prompts/payloads/secrets.

Frontend:

- Next.js / React / TypeScript / Tailwind.
- Public routes и workspace routes существуют как production UI baseline.
- Workspace интегрирован с backend capabilities, credits и Product Card workflow.

AI/provider:

- Google Gemini / Google Gen AI SDK как текущий provider implementation.
- Agent runtime построен вокруг `AgentInvocationService`.
- Контракты агентов versioned через `contracts.py` и `prompt_config.py`.
- Human Identity Agent прошёл production acceptance на 8 изображениях.

## 4. Что уже сделано

### Platform foundation

- Перенос на portable backend baseline.
- Выделены `domain`, `use_cases`, `adapters`, `entrypoints`.
- Добавлены runtime dependency builders и lazy factories.
- Снижена зависимость активных product workflows от legacy Firestore/GCS.

### Frontend/workspace

- Реальные public/workspace routes.
- Product Card UI подключён к backend workflow.
- Sidebar/dashboard/credits/capabilities синхронизированы через backend-owned state.
- Locked/disabled states введены для функций без production pipeline.

### Product Card

- `POST /api/product-cards` и status/result endpoints используются фронтом.
- Garment Identity analysis стал обязательным pre-generation этапом.
- Product Card Agent получает persisted structured garment analysis, а не переинтерпретирует исходное фото.
- Job/result/status persistence работает через SQL contour.

### Try-On analysis foundation

- Human Identity, Garment Identity и Material / Texture analyses выполняются как mandatory pre-generation bundle.
- Human Identity persisted child entity добавлена.
- Try-On Instruction Agent получает только approved structured snapshots.
- Generation failures переводятся в persisted failed job с zero charged credits.

### Human Identity Agent

- Подключён через canonical `AgentInvocationService`.
- Contract v2 включает:
  - `subject_count`;
  - `crop_quality`;
  - `try_on_body_coverage`;
  - `occlusion_risk`;
  - `required_regions_missing`.
- Policy hardening блокирует:
  - cropped/headshot;
  - скрытое/частично закрытое лицо;
  - multiple people;
  - no-human;
  - insufficient body coverage;
  - high occlusion risk.
- Acceptance на 8 assets прошёл:
  - critical false pass: `0`;
  - `good_front.jpg` allowed;
  - `side_pose.jpg` allowed;
  - плохие/ambiguous фото blocked до Try-On generation.

### Cost / credits economics

- Добавлен `src/costs`.
- Добавлены:
  - provider price config;
  - `WorkflowCostEstimator`;
  - credits pricing policy;
  - `scripts/report_workflow_costs.py`;
  - `docs/costs/*`.
- Cost metadata сохраняется в agent invocation ledger.
- Live billing не менялся.
- Baseline: `1 credit = 50 KZT`.

### Investor materials

- Создан PDF для инвесторов:
  - `output/pdf/ai_fitfabrica_investor_unit_economics_ru.pdf`.
- Документ включает себестоимость, credits, маржу, драйверы затрат, B2B packages, риски и recalibration plan.

## 5. Что ещё не сделано

### Agent validation and rollout

- Garment Identity Agent нужно прогнать как второй production acceptance этап.
- Material / Texture Agent нужно проверить на honesty policy: не утверждать точный состав ткани без label/source.
- Try-On Instruction Agent нужно проверять на structured quality and safety.
- Quality Verifier Agent нужно отдельно калибровать на bad/good outputs.
- Repair Agent и image editing pipeline ещё не являются production-ready.

### Image generation

- Production Try-On image generation требует финальной provider strategy.
- Для image generation/editing нужно выделить отдельные ports и cost controls.
- Nano Banana / image models должны подключаться только через backend adapter, не из workflow и не из frontend.

### Marketplace and search

- Marketplace Agent пока не должен использовать скрытый scraping.
- Нужно выбрать approved data sources:
  - official APIs;
  - partner feeds;
  - seller catalog import;
  - approved public links/connectors.
- Similar/Cheaper Search требует connector cost accounting и no-result cost accounting.

### Billing/pricing

- Текущий pricing baseline не является финальным.
- После 20-50 staging/prod прогонов нужен recalibration report:
  - actual avg Try-On cost;
  - actual avg Product Card cost;
  - repair rate;
  - retry rate;
  - failed free job cost;
  - real margin by workflow.

### Production readiness

- Нужны rate-limit/backoff/circuit-breakers для Gemini/Vertex `429 RESOURCE_EXHAUSTED`.
- Нужны monitoring dashboards по agents, latency, invalid output, cost, retries.
- Нужны admin-only cost endpoints только после готового admin auth.
- Нужен стабильный deploy/release process для backend + frontend.

## 6. Следующий порядок работ

1. Garment Identity Agent acceptance.
2. Material / Texture Agent acceptance.
3. Try-On Instruction Agent acceptance.
4. Quality Verifier Agent baseline.
5. Repair/Image Edit architecture.
6. Model routing config для дешёвых/дорогих моделей.
7. End-to-end Try-On production smoke.
8. Marketplace connector design.
9. Recalibration report после 20-50 реальных прогонов.

## 7. Definition of Done для новых этапов

Этап считается закрытым только если:

- есть contract/schema;
- есть backend policy/fail-closed behavior;
- есть tests;
- есть staging/live acceptance, если агент вызывает реальную модель;
- credits не списываются на pre-generation/system failures;
- docs обновлены;
- новая модель может открыть `docs/README.md` и понять текущее состояние проекта.
## 8. Масштабирование и отказоустойчивость по принципам Kleppmann

Этот блок является обязательным перед крупными B2B-клиентами, marketplace/search нагрузкой и массовым подключением агентов.

Применяем не преждевременное усложнение, а правильные швы роста:

- Все B2B сущности должны быть tenant-aware: `owner_id`, `merchant_id`, `product_id`, `import_id`, `job_id`.
- Крупный клиент должен иметь возможность перейти в hot-account mode: отдельная queue partition, storage prefix, rate-limit bucket и при необходимости отдельный shard/БД без переписывания бизнес-логики.
- Обычные клиенты остаются на shared partition, чтобы не усложнять систему раньше времени.
- Все дорогие и повторяемые операции должны иметь idempotency: upload, import, submit, generation, repair, credits.
- При перегрузке backend возвращает structured backpressure response, а не падает и не создаёт дубли.
- Catalog CRUD должен работать в degraded mode даже если AI provider, image generation или marketplace connector временно недоступны.
- Добавляется controlled failure injection: storage failure, SQL failure, Redis/queue failure, AI provider timeout, worker crash, partial import failure.
- Chaos Monkey в production пока не включается. Сначала делаем deterministic failure tests и staging chaos-smoke.

Правильный порядок внедрения:

1. Tenant partitioning policy.
2. Idempotency contract.
3. Failure-injection tests.
4. Backpressure/degraded-mode rules.
5. Staging chaos-smoke.
6. Только после этого рассматривать production chaos drills.
## 9. 2026-06-29 B2B Product Catalog Status

The B2B catalog is now the active foundation for future marketplace/search work and business seller onboarding.

Completed scope:

- Merchant profile, product draft/update/list, offer data, product image upload, submit-to-review, admin approve/reject, and CSV import.
- SQL migration, SQL repository, backend use-case service, and typed business/admin API routes.
- Frontend workspace routes: `/workspace/business-catalog`, `/workspace/business-catalog/new`, `/workspace/business-catalog/import`.
- Frontend internal admin routes: `/admin/business-catalog`, `/admin/business-accounts`.
- Search projection contract for future Similar/Cheaper Search: only approved active products with offers can be indexed.
- Tenant tier policy inspired by high-load design: shared `standard` tier and future hot-account `large` tier.
- Manual admin tier assignment; backend recommendations are advisory only.
- Idempotency for CSV import, image upload, and submit-to-review.
- Controlled failure handling and structured safe errors.
- Backpressure limits for CSV imports and product image counts.
- User-facing upload guidance on frontend import and product-photo screens.

Not enabled yet:

- External marketplace/Instagram search.
- Hidden scraping.
- Automatic tier promotion/demotion.
- Production chaos drills.
- Queue-backed hourly/concurrent import limits.
- Direct publishing to seller marketplace accounts.

Correct next order:

1. Finish local verification for B2B catalog reliability and documentation.
2. Run staging smoke only when VM/deployed backend is needed.
3. Design legal marketplace/Instagram connector contracts and geo-ranking.
4. Then continue Similar/Cheaper Search and competitor analysis on top of the catalog foundation.
