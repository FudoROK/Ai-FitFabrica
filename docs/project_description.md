# Документ 1: Описание Проекта

Этот проект представляет собой "Базовый Скелет Бэкенда AI-Ассистента", разработанный как готовая к развертыванию, чистая и нейтральная основа для новых проектов AI-Ассистентов для клиентов. Он предоставляет полноценную среду выполнения от начала до конца, что позволяет быстро запускать новые клиентские проекты, которые затем могут сосредоточиться на интеграции специфичной для клиента логики, полей данных, внешних сервисов и каналов связи.

**Ключевые Принципы:**
*   **Развертывание с Нуля:** Полностью функционален и готов к немедленному развертыванию.
*   **Нейтральность:** Отсутствие какой-либо специфичной для клиента символики, предопределенных запросов или уникальной бизнес-логики.
*   **Бэкенд-Ориентированность:** Вся критически важная бизнес-логика, вычислительные задачи и меры безопасности обрабатываются исключительно бэкендом.
*   **Взаимозаменяемые Адаптеры:** Разработан для легкой замены интеграций с различными сервисами, такими как CRM, платформы обмена сообщениями и поставщики Больших Языковых Моделей (LLM).
*   **Независимость от Клиента:** Каждая клиентская реализация работает изолированно, с выделенными репозиториями GitHub, проектами Google Cloud и управлением секретами.
*   **Расширение Только Вперед:** Структурирован для упрощения добавления новых функций без необходимости рефакторинга или очистки существующего устаревшего кода.

**Пайплайн Событий (Базовая Версия):**
Стандартный поток событий: `Telegram -> Webhook -> Pub/Sub -> Backend -> Primary Agent -> Firestore -> Reply -> Telegram`.

**Архитектурные Ограничения:**
*   Бэкенд является единственным оркестратором всех побочных эффектов.
*   Роль LLM строго ограничена вычислениями, возвращая только `reply_text` и `system_payload`.
*   Доменная логика строго организована по отдельным слоям: `entrypoints`, `use_cases`, `domain`, `adapters`, `runtime_agents` и `adk_agents`.
*   Агенты работают независимо и не оркестрируют друг друга; бэкенд сохраняет единоличное управление оркестрацией.

## Stage 1 Portable Foundation

Stage 1 adds the portable platform baseline without migrating product workflows yet.

- `src/adapters/database/sql` establishes PostgreSQL runtime primitives and Alembic metadata.
- `src/adapters/cache` establishes Redis client bootstrap.
- `src/adapters/storage` establishes a backend-neutral object storage contract with in-memory and S3-compatible adapters.
- `src/adapters/vector` establishes Qdrant client bootstrap and collection naming.
- `src/services/runtime/portable_infrastructure.py` exposes the runtime-owned dependency bundle for those services.

## Stage 2 Identity Core Migration

Stage 2 moves canonical identity state toward PostgreSQL while keeping the hot path isolated behind contracts.

- `src/adapters/database/sql/identity_models.py` defines portable SQL tables for persons, leads, channel identities, bindings, and audit.
- `src/adapters/database/sql/identity_repositories.py` implements the identity-core repository contracts on SQLAlchemy sessions.
- `src/adapters/database/sql/identity_audit.py` defines SQL-backed audit primitives for identity resolution outcomes.
- `src/entrypoints/runtime_dependencies.py` selects SQL identity repositories when portable SQL runtime infrastructure is configured.

## Stage 4 Vector Foundation

Stage 4 turns the earlier Qdrant bootstrap into a real retrieval foundation.

- `src/domain/vector_search.py` defines typed namespaces, vector points, filters, queries, and search hits.
- `src/adapters/vector/namespaces.py` locks approved vector collections and their sizing rules.
- `src/adapters/vector/qdrant_bootstrapper.py` ensures required collections exist before retrieval starts.
- `src/adapters/vector/qdrant_filters.py` maps backend filters into Qdrant payload filters.
- `src/adapters/vector/qdrant_retriever.py` provides the first reusable upsert/search adapter for garments and products.

## Stage 5 Provider Abstraction

Stage 5 introduces a backend-owned provider runtime so business services stop constructing specific AI providers directly.

- `src/domain/provider_models.py` defines typed request/result models for reasoning, embeddings, and image operations.
- `src/domain/provider_ports.py` defines provider-neutral ports for structured reasoning, agent runtime, embeddings, image generation, and image editing.
- `src/llm/provider_runtime.py` composes the active runtime adapters from settings.
- `src/adapters/ai` contains the first deterministic embedding and image stub adapters for backend wiring and tests.
- `src/entrypoints/runtime_dependencies.py` now exposes cached provider-runtime wiring alongside other runtime dependencies.

## Stage 6 Try-On Rebase

Stage 6 moves the existing Try-On workflow off ad hoc sandbox persistence and onto the portable backend baseline.

- `src/adapters/database/sql/try_on_models.py` defines SQL tables for jobs, stored inputs, status history, cost events, results, and errors.
- `src/adapters/database/sql/try_on_repositories.py` persists the Try-On aggregate on SQLAlchemy sessions.
- `src/adapters/database/sql/try_on_serialization.py` isolates row/domain mapping so repository logic stays small.
- `src/entrypoints/runtime_dependencies.py` now owns Try-On repository, storage, and generation wiring.
- `src/entrypoints/try_on_routes.py` stays thin and consumes the composition root instead of choosing storage adapters directly.
- `src/adapters/try_on/provider_generation.py` adds a provider-runtime-backed Try-On generation contour behind an explicit backend switch.

## Stage 7 Similar Search Foundation

Stage 7 turns the earlier vector baseline into the first backend-owned similar-search workflow.

- `src/domain/similar_search.py` defines typed request, catalog, query-profile, hydration, and response models.
- `src/adapters/database/sql/catalog_models.py` defines SQL tables for canonical products, marketplace offers, and price snapshots.
- `src/adapters/database/sql/catalog_repositories.py` hydrates retrieval hits from PostgreSQL product and offer truth.
- `src/use_cases/similar_search` owns query preparation, ranking, and workflow orchestration.
- `src/entrypoints/similar_search_routes.py` exposes a thin FastAPI endpoint for structured similar search.

## Stage 8 Product-Card Workflow Foundation

Stage 8 starts the first B2B execution contour by moving product-card generation into backend-owned workflow code.

- `src/domain/product_card.py` defines typed request, draft, job, and version records for product-card generation.
- `src/adapters/database/sql/product_card_models.py` defines SQL tables for jobs, source assets, generated versions, and quality notes.
- `src/adapters/database/sql/product_card_repositories.py` persists product-card workflow truth on SQLAlchemy sessions.
- `src/use_cases/product_card` owns storage, generation, and persistence orchestration.
- `src/entrypoints/product_card_routes.py` exposes a thin FastAPI endpoint for structured product-card creation.

## Stage 8 Content-Package Workflow Foundation

Stage 8 continues the B2B execution contour by moving content-package assembly into backend-owned workflow code.

- `src/domain/content_package.py` defines typed request, asset, job, and version records for content-package generation.
- `src/adapters/database/sql/content_package_models.py` defines SQL tables for jobs, versions, and artifact references.
- `src/adapters/database/sql/content_package_repositories.py` persists content-package workflow truth on SQLAlchemy sessions.
- `src/use_cases/content_package` owns generation, artifact storage, and persistence orchestration.
- `src/entrypoints/content_package_routes.py` exposes a thin FastAPI endpoint for structured content-package creation.

## Stage 8 Pricing Workflow Foundation

Stage 8 completes the first B2B backend contour by moving pricing recommendation logic into backend-owned workflow code.

- `src/domain/pricing.py` defines typed request, comparable, recommendation, job, and result records for pricing.
- `src/adapters/database/sql/pricing_models.py` defines SQL tables for jobs and persisted recommendations.
- `src/adapters/database/sql/pricing_repositories.py` persists pricing workflow truth on SQLAlchemy sessions.
- `src/domain/billing.py`, `src/use_cases/billing/service.py`, and `src/adapters/database/sql/billing_repositories.py` define the backend-owned credits and billing core.
- `src/entrypoints/credits_routes.py` exposes portable balance and ledger APIs for credits history.
- Billing integration for Try-On and B2B workflows is implemented behind a guarded activation path so durable ledger enforcement can be enabled after account seeding and economics rollout.
- `src/domain/operations.py`, `src/use_cases/operations/*.py`, and `src/adapters/database/sql/operations_repositories.py` define the portable queue and worker operations foundation.
- `src/entrypoints/status_routes.py` now exposes runtime operations readiness details alongside infrastructure health.
- The project now has a backend-owned worker runtime contour, and B2B create routes use accepted-job plus background-worker execution.
- The Try-On route now follows the accepted-job plus worker-execution contour for normal sandbox execution.
- The `pending` sandbox mode remains as an explicit polling-only test hook and is not treated as the final production generation path.
- `TRY_ON_GENERATION_BACKEND=provider_runtime` is available for controlled placeholder rollout without changing route or persistence boundaries.
- `TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on` now activates the first real Vertex-backed Try-On generation path while preserving the existing worker, billing, and storage boundaries.
- Try-On now includes a model-backed backend quality-verifier contour after generation plus a first backend repair contour for locally fixable issues.
- The model-backed quality-verifier path now degrades safely to deterministic verification when structured provider access is unavailable.
- The repair path now prefers provider-runtime local correction and falls back to deterministic repair when needed.
- `src/use_cases/pricing` owns brief preparation, comparable lookup, recommendation logic, and persistence orchestration.
- `src/entrypoints/pricing_routes.py` exposes a thin FastAPI endpoint for structured pricing recommendations.

## Stage 11 FitFabrica Agent System Status

The active product-agent baseline now lives under `src/adk_agents` and is split into three implemented waves.

- Wave 1 Try-On agents:
  - `human_identity_agent`
  - `garment_identity_agent`
  - `material_texture_agent`
  - `try_on_agent`
  - `quality_verifier_agent`
  - `repair_agent`
  - `fashion_stylist_agent`
- Wave 2 routing and profile agents:
  - `orchestrator_agent`
  - `user_profile_agent`
  - `business_profile_agent`
- Wave 3 commerce agents:
  - `marketplace_agent`
  - `trend_agent`
  - `pricing_agent`
  - `product_card_agent`
  - `cost_credits_agent`

All of these agents are structured-output-only roles. They do not own orchestration, persistence, billing, retry, or repair decisions. Backend workflow code remains authoritative.

Compatibility note:

- `daily_memory_agent` and `rolling_memory_agent` remain support-only contours.
- `daily_memory_agent_tmp20260425_024853` is no longer part of the active runtime surface.
- `src/adk_agents/primary_agent` is no longer part of the active ADK surface.
- `src/runtime_agents/dialog_reply` is now the canonical backend reply-runtime contour.
- `dialog_reply_task` is the canonical backend reply-task name.
- `src/runtime_agents/dialog_reply` is the only active backend reply-runtime contour.
- `dialog_reply_task` is the only active backend reply-task name.

Stage 11 is now treated as complete for the active architecture baseline. The next practical step is portable backend rollout plus frontend integration on top of the new backend-owned runtime contour.
