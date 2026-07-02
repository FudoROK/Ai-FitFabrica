# AI FitFabrica - Что осталось сделать

Дата актуализации: 2026-06-17

Это короткий документ для владельца проекта. Он отвечает на вопрос: что делать дальше по проекту, без технического шума.

## Главный статус

Проект уже имеет рабочий backend/frontend baseline, подключённый первый production-agent baseline и начальную экономику credits/costs.

Но проект ещё не готов к массовому production-запуску, потому что нужно пройти agent-by-agent acceptance и довести generation/quality/repair pipeline.

## 2026-07-02 Update: Pre-Billing Readiness

Локальная предбиллинговая готовность для следующего paid testing этапа подтверждена:

- backend architecture guardrail прошёл;
- backend/scripts compileall прошёл;
- полный backend pytest прошёл: `1129 passed`;
- frontend `npm ci`, `lint`, `typecheck`, `build` прошли;
- `npm ci` показал 5 audit findings (`1 low`, `4 moderate`), автоматический `npm audit fix --force` не запускался;
- рабочее дерево остаётся грязным и требует осознанного решения, какие изменения входят в deploy baseline.

Главный следующий блокер: восстановить Google/Gemini/Vertex billing/provider access. После этого нужно запускать paid provider smoke checks, затем Try-On HTTP/worker acceptance, B2B live category validation и Similar Search garment-photo acceptance.

## Самый правильный следующий шаг

### 1. Garment Identity Agent

Status update 2026-06-28:

- Local contract/policy hardening is done.
- Backend now blocks no-garment, ambiguous multiple garments, tight crop, insufficient workflow coverage, high occlusion, low confidence and high uncertainty before generation.
- Next remaining action: run the real garment image dataset on VM/staging and record expected vs actual live acceptance.

Почему следующий именно он:

- он нужен и для Try-On, и для Product Card;
- без него нельзя надёжно понимать одежду;
- он влияет на качество генерации, карточек, поиска похожих товаров и pricing;
- его ошибки дешевле поймать до generation.

Что нужно сделать:

- собрать тестовый dataset одежды;
- проверить распознавание типа, цвета, кроя, рукавов, воротника, пуговиц, карманов, принта/лого, текстуры;
- добавить policy для low-confidence/ambiguous garments;
- провести live acceptance;
- обновить docs/action log.

## После Garment Identity

### 2. Material / Texture Agent

Status update 2026-06-17:

- Local honesty policy is done.
- Backend now blocks empty material analysis, missing evidence, low confidence, high uncertainty and invalid trusted-composition claims.
- Next remaining action: run live material/texture acceptance after Garment Identity live acceptance.

Главное правило: агент не должен выдумывать точный состав ткани. Он может писать только визуальную оценку, если нет label/source.

### 3. Try-On Instruction Agent

Status update 2026-06-17:

- Local policy is done.
- Backend now blocks instructions that disable face/body/pose preservation, omit garment focus points, omit generation exclusions, omit evidence, have low confidence or high uncertainty.
- Adapter still passes only structured Human/Garment/Material snapshots, not source images.
- Next remaining action: live instruction acceptance after upstream visual agents are accepted.

Проверить, что он не получает исходные фото, а работает только со structured facts:

- human analysis;
- garment analysis;
- material/texture analysis.

### 4. Quality Verifier Agent

Status update 2026-06-17:

- Local backend quality policy is done.
- Dedicated AgentInvocationService-based Quality Verifier adapter is integrated into Try-On runtime.
- Selected wear-control live acceptance passed on VM/staging with `8/8` matched and zero false pass/repair/reject.
- Next remaining action: keep expanding visual golden fixtures as real paid Try-On failures appear.

Это обязательный production gate. Пользователь не должен видеть явно сломанный результат.

### 5. Repair Agent и image editing

Status update 2026-06-28:

- Local repair policy is done.
- Backend allows repair only for local repairable defects and blocks unsafe repair before editing.
- Dedicated AgentInvocationService-based Repair Agent planner is integrated before provider image-edit repair.
- Provider-runtime image edit now receives Repair Agent approved region instructions.
- Workflow already runs second Quality Verifier after repair.
- Next remaining action: run VM/staging live acceptance for the full Repair Agent planner -> image edit -> second Quality Verifier path.

Нужно разделить:

- repair_instruction через Gemini;
- repair_image_generation/image_edit через визуальную модель;
- second_quality_verifier после repair.

## Что делать с VM

VM включать только когда нужен live backend/staging прогон.

Перед включением VM читать:

- `docs/reports/2026-06-17-try-on-local-readiness-report.md`

Для обычной разработки:

- docs;
- tests;
- contracts;
- frontend code;
- backend unit tests;

VM не нужна.

## Что делать с инвесторами

Уже есть PDF:

- `output/pdf/ai_fitfabrica_investor_unit_economics_ru.pdf`

Перед показом инвесторам желательно:

- вручную перечитать PDF;
- добавить реальные screenshots/demo, если нужно;
- после 20-50 прогонов обновить цифры в recalibration report.

## Что нельзя делать сейчас

- Не подключать все агенты хаотично сразу.
- Не открывать admin cost endpoints без admin auth.
- Не включать скрытый scraping marketplace.
- Не списывать credits за pre-generation/system failures.
- Не давать frontend прямой доступ к AI provider.
- Не выбирать дорогую модель для всех агентов без model routing.

## Приоритеты на ближайшие этапы

1. Garment Identity acceptance.
2. Material / Texture honesty acceptance.
3. Quality Verifier baseline.
4. Model routing config.
5. Real Try-On generation pipeline.
6. Repair/Image Edit pipeline.
7. Marketplace connector plan.
8. Recalibration after real runs.

## 2026-06-23 Update: Garment Wear Controls

New enterprise plan added:

- `docs/superpowers/plans/2026-06-23-garment-wear-controls-taxonomy-admin-plan.md`
- `docs/superpowers/plans/2026-06-23-wear-controls-taxonomy-admin-v2-implementation-plan.md` is the current execution-ready v2 plan and supersedes the first draft for implementation order.

Updated near-term order:

1. Garment Identity live acceptance.
2. Garment Wear Controls taxonomy foundation: controlled garment types, allowed wear modes, unknown-type candidates, and future `/admin/taxonomy` review.
3. Material / Texture honesty acceptance.
4. Try-On Instruction integration with selected wear control.
5. Quality Verifier baseline including wear-control match checks.
6. Model routing config.
7. Repair/Image Edit pipeline including safe wear-control corrections.
8. Marketplace connector plan.
9. Recalibration after real runs.

## Простыми словами

Сейчас проект надо не расширять вширь, а укреплять по слоям:

1. каждый агент отдельно;
2. потом связка workflow;
3. потом качество результата;
4. потом экономика;
5. потом production/demo/investors.
## Масштабирование и отказоустойчивость

Перед крупными B2B-клиентами, поиском по маркетплейсам/Instagram и массовым подключением агентов нужно добавить отдельный reliability gate.

Что нужно сделать:

- Разделить нагрузку по владельцам бизнеса: обычные клиенты на общей инфраструктуре, крупные клиенты в hot-account mode.
- Заложить возможность отдельной очереди, storage prefix, rate-limit bucket и при необходимости отдельной БД для большого клиента.
- Добавить idempotency, чтобы повторная загрузка фото, CSV import или submit не создавали дубли.
- Добавить backpressure: если система перегружена, backend честно говорит “подождите”, а не ломается.
- Добавить controlled failure tests: падение storage, SQL, Redis/queue, AI provider, worker.
- Chaos Monkey в production пока не включать. Сначала только контролируемые тесты и staging chaos-smoke.

Простыми словами: мы заранее готовим проект к росту, но не усложняем его раньше времени.
## 2026-06-29 Update: B2B Catalog Foundation

What is now done:

- Business users can own a catalog foundation: merchant profile, products, offers, product images, CSV import, and submit-to-review.
- Admin review exists for product approval/rejection before products can be projected into future search.
- Search projection is safe by default: only `active` + `approved` products with valid offers are eligible.
- Tenant reliability foundation exists: `standard` and `large` tiers, advisory backend recommendations, and manual admin assignment.
- Retry safety exists for important mutations through `Idempotency-Key`: CSV import, product image upload, and submit-to-review.
- Controlled failure tests exist for storage failure, metadata persistence failure, and import row-error persistence failure.
- Backpressure exists before expensive work: tier-based CSV size/row limits and image-count limits.
- Frontend explains upload limits on CSV import and product photo upload screens.

What still remains:

- Populate the staging catalog with realistic approved products before judging Similar Search quality.
- Run a manual website Similar Search test against realistic catalog data after catalog population.
- Add real production admin auth/audit hardening before exposing admin routes outside internal use.
- Add queue/worker-backed hourly and concurrent import limits after real import workers are introduced.
- Design marketplace, Instagram, Kaspi, Wildberries, and partner-feed connectors only through legal/approved data sources.
- Define marketplace connector costs, no-result search costs, parser/proxy costs, and geo-ranking rules before enabling Similar/Cheaper Search.
- Keep automatic tier promotion disabled; admin should continue to approve `standard`/`large` tier changes manually.

VM note:

- VM is not needed for local docs, unit tests, lint, typecheck, or build.
- VM is needed only for deployed/staging smoke, real SQL/object-storage upload smoke, or paid AI/provider checks.

## 2026-06-29 Update: Similar Search Location Priority

Decision:

- Similar/Cheaper Search prioritizes the customer's location first.
- Search order is: same city, same country with delivery to the city, same country, delivery available, then remote offers.
- Price and visual/text similarity are still important, but they do not beat a practical local result when the local result is relevant.

Current implementation status:

- Backend contracts now define approved source types for future marketplace and Instagram connectors.
- Local approved B2B catalog products project as `local_catalog`.
- Ranking can explain whether a result matched by same city, same country, delivery, or remote source.

What remains:

- Design legal Kaspi/Wildberries/Instagram connector adapters.
- Add click/lead tracking and cost ledger for free search monetization.
- Expand catalog density and connector coverage beyond the current local B2B catalog.

## 2026-06-29 Update: Similar Search Garment Photo Workflow

Done:

- `/workspace/similar-search` is no longer a placeholder. It now has a real upload form for garment photo search.
- Backend endpoint `POST /api/similar-search/garment-photo` accepts a garment image, validates it, stores it through backend object storage, runs Garment Identity through backend runtime, and searches with a typed garment profile.
- Similar Search now has a local B2B catalog fallback when the vector index has no hits. It returns only approved active catalog products with sellable offers.
- Location-first ranking is preserved: same city, country, delivery, then remote.
- Basic search remains free for the user by product strategy; premium Try-On, deep external search, and B2B analytics stay separate monetization layers.

Still remaining:

- Design legal approved connectors for Kaspi, Wildberries, Instagram Business, partner feeds, and official APIs.
- Add click/lead tracking and cost ledger for free search monetization.
- Run browser-level website Similar Search acceptance after the next frontend deploy, using the already loaded realistic catalog.

Staging acceptance update:

- Real garment-photo Similar Search now runs through Gemini multimodal agent runtime.
- Backend upload endpoint returned HTTP `200` on a realistic shirt image.
- Results preserve location fields and primary product image URLs.
- Smoke catalog records were archived; current results come from realistic approved local catalog products.
- Immediate remaining product limitation: result quality is only as good as approved catalog density and future legal connectors.

Search indexing update:

- Done: backend indexing pipeline for approved B2B catalog products is implemented locally.
- Done: approved catalog records can be embedded and written into the Qdrant `products` namespace through backend ports/adapters.
- Done: manual reindex command is available: `.venv\Scripts\python.exe scripts/reindex_business_catalog_search.py --limit 1000`.
- Done: approved products now have search index lifecycle status: `not_indexed`, `pending`, `indexed`, `failed`.
- Done: approving a product marks it `pending` for search indexing; successful reindex marks it `indexed`; indexing error marks it `failed`.
- Done: admin can filter products by search index status and retry failed indexing from the admin catalog UI.
- Done: approving or retrying a product now automatically puts a `business_catalog_search_index` job into the backend operations queue.
- Done: worker runtime now has a `business_catalog_search_index` handler that indexes the approved product and updates its lifecycle status.
- Done: deploy readiness script now checks B2B search-index migration, DB schema, worker handler, and indexing workflow before staging is accepted.
- Done: staging backend/frontend deployment passed after search-index lifecycle changes.
- Done: staging manual reindex and worker indexing passed for approved products.
- Done: realistic test catalog was loaded, approved, indexed, and used by live Similar Search.
- Remaining: browser-level website acceptance and future connector expansion.
- VM: not needed until staging deploy, staging reindex, or live website smoke.
