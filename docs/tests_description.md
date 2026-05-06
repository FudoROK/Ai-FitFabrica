# Документ 3: Описание Тестов

Этот документ содержит список всех тестовых файлов в директории `tests/`, их назначение и описание того, какую часть проекта они покрывают.

*   **`conftest.py`**:
    *   **Назначение**: Файл конфигурации для `pytest`. Он содержит фикстуры (fixtures) и хуки (hooks), которые используются несколькими тестами для настройки тестовой среды, предоставления общих объектов или выполнения действий до/после тестов.
    *   **Покрытие**: Обеспечивает общую инфраструктуру для всех тестов, косвенно покрывая различные аспекты настройки среды.
*   **`test_active_window_close_policy.py`**:
    *   **Назначение**: Тестирует логику политики закрытия активного "окна" взаимодействия (например, сессии пользователя).
    *   **Покрытие**: `src/memory_layer/domain/window_close_policy.py` и связанные с ним компоненты в слое памяти, которые определяют, когда сессия считается завершенной.
*   **`test_adk_agent_root_contract.py`**:
    *   **Назначение**: Проверяет соблюдение корневого контракта или интерфейса для агентов ADK (Agent Development Kit).
    *   **Покрытие**: Базовые контракты и абстракции для агентов в `src/adk_agents/`.
*   **`test_build_context_use_case.py`**:
    *   **Назначение**: Тестирует сценарий использования (use case) для сборки контекста, который затем передается агентам или LLM.
    *   **Покрытие**: Логика сборки контекста в `src/services/context/core_context_builder.py` и `src/services/context/context_assembler.py`.
*   **`test_channel_identity.py`**:
    *   **Назначение**: Проверяет логику и модели, связанные с идентификацией канала и пользователя.
    *   **Покрытие**: `src/domain/channel_identity.py`, `src/identity_core/models/channel_identity.py` и связанные сервисы идентификации.
*   **`test_context_assembler.py`**:
    *   **Назначение**: Тестирует сервис-сборщик контекста.
    *   **Покрытие**: `src/services/context/context_assembler.py`.
*   **`test_context_projection.py`**:
    *   **Назначение**: Проверяет сервис, отвечающий за создание "проекций" контекста.
    *   **Покрытие**: `src/services/context/context_projection.py`.
*   **`test_core_runtime_smoke.py`**:
    *   **Назначение**: Дымовые тесты для основного рантайма приложения, проверяющие его базовую работоспособность и связность ключевых компонентов.
    *   **Покрытие**: Высокоуровневая функциональность, связывающая `src/main.py`, `src/entrypoints/` и основные сервисы.
*   **`test_dialog_service_decomposition.py`**:
    *   **Назначение**: Тестирует декомпозицию (разложение на части) диалогового сервиса, возможно, проверяя, как сложные диалоги разбиваются на более мелкие управляемые части.
    *   **Покрытие**: `src/services/dialog/dialog_service.py` и связанные с ним компоненты, отвечающие за структуру диалога.
*   **`test_dialog_service_smoke.py`**:
    *   **Назначение**: Дымовые тесты для диалогового сервиса, проверяющие его базовую функциональность.
    *   **Покрытие**: Основные функции `src/services/dialog/dialog_service.py`.
*   **`test_distributed_rate_limiter.py`**:
    *   **Назначение**: Тестирует распределенный лимитер запросов, который работает в масштабируемой среде (например, с использованием Firestore).
    *   **Покрытие**: `src/services/rate_limit/firestore_rate_limiter.py` и его взаимодействие с инфраструктурой.
*   **`test_event_state_machine_transaction_contract.py`**:
    *   **Назначение**: Проверяет контракт транзакционной конечного автомата событий.
    *   **Покрытие**: Контракты и, возможно, базовые реализации конечных автоматов, которые обрабатывают события, например, в `src/domain/contracts/` или `src/services/dialog/`.
*   **`test_event_state_machine.py`**:
    *   **Назначение**: Тестирует логику конечного автомата событий.
    *   **Покрытие**: Основная реализация конечного автомата, которая управляет потоком событий в приложении, возможно, в `src/services/dialog/`.
*   **`test_fake_provider.py`**:
    *   **Назначение**: Тестирует "фейковый" провайдер LLM, который используется для изоляции других компонентов от реальных LLM-вызовов во время тестирования.
    *   **Покрытие**: `src/llm/providers/fake_provider.py`.
*   **`test_gemini_structured_provider.py`**:
    *   **Назначение**: Тестирует провайдер LLM для Google Gemini, который специально настроен для получения структурированных ответов.
    *   **Покрытие**: `src/llm/providers/gemini_structured_provider.py`.
*   **`test_google_maps_timezone_resolver.py`**:
    *   **Назначение**: Тестирует разрешитель часовых поясов, использующий API Google Maps.
    *   **Покрытие**: `src/adapters/external_apis/google_maps/` и `src/services/timezone/resolver.py`.
*   **`test_identity_resolution_service.py`**:
    *   **Назначение**: Тестирует сервис разрешения идентификации, который сопоставляет различные идентификаторы с уникальным пользователем.
    *   **Покрытие**: `src/identity_core/services/identity_resolution.py`.
*   **`test_ingress_boundary_validation.py`**:
    *   **Назначение**: Тестирует валидацию на границе входящих данных, обеспечивая, что все внешние запросы соответствуют ожидаемым форматам и правилам.
    *   **Покрытие**: `src/entrypoints/payloads.py`, `src/domain/context_validation.py` и `src/services/inbound/inbound_gate_service.py`.
*   **`test_internal_task_oidc_auth.py`**:
    *   **Назначение**: Тестирует аутентификацию OIDC (OpenID Connect) для внутренних задач.
    *   **Покрытие**: Политики безопасности в `src/entrypoints/policies.py` и логика аутентификации для внутренних маршрутов.
*   **`test_llm_core_types.py`**:
    *   **Назначение**: Тестирует основные типы данных и Enum'ы, используемые в LLM-слое.
    *   **Покрытие**: `src/llm/core/types.py`.
*   **`test_llm_provider_leakage.py`**:
    *   **Назначение**: Проверяет, что реализация LLM-провайдера не "просачивается" (leakage) за свои границы, то есть доменный слой не зависит от специфики конкретного провайдера.
    *   **Покрытие**: Взаимодействие между `src/llm/providers/` и `src/llm/llm_service.py`.
*   **`test_llm_provider_registry.py`**:
    *   **Назначение**: Тестирует реестр провайдеров LLM.
    *   **Покрытие**: `src/llm/providers/registry.py`.
*   **`test_llm_service.py`**:
    *   **Назначение**: Тестирует основной сервис для взаимодействия с LLM.
    *   **Покрытие**: `src/llm/llm_service.py`.
*   **`test_llm_task_registry.py`**:
    *   **Назначение**: Тестирует реестр задач LLM.
    *   **Покрытие**: `src/llm/llm_task_registry.py`.
*   **`test_llm_transport_executor.py`**:
    *   **Назначение**: Тестирует исполнителя транспортного слоя для LLM.
    *   **Покрытие**: `src/llm/transport/executor.py`.
*   **`test_log_redaction.py`**:
    *   **Назначение**: Проверяет функциональность сокрытия конфиденциальных данных в логах.
    *   **Покрытие**: Логика логирования и, возможно, утилиты в `src/utils/` или `src/settings.py`, связанные с безопасностью логов.
*   **`test_memory_agent_contract_boundary.py`**:
    *   **Назначение**: Проверяет границы контракта агента памяти.
    *   **Покрытие**: `src/runtime_agents/memory_agent/contracts/` и взаимодействие с `src/runtime_agents/memory_agent/agent.py`.
*   **`test_memory_agent_parser_contract.py`**:
    *   **Назначение**: Проверяет контракт парсера для агента памяти.
    *   **Покрытие**: `src/runtime_agents/memory_agent/memory_response_parser.py` и его контракты.
*   **`test_memory_artifacts_write_use_cases.py`**:
    *   **Назначение**: Тестирует сценарии использования для записи артефактов памяти.
    *   **Покрытие**: `src/memory_layer/use_cases/daily_artifacts_write_use_case.py` и `src/memory_layer/use_cases/rolling_artifacts_write_use_case.py`.
*   **`test_memory_daily_sync_llm_service.py`**:
    *   **Назначение**: Тестирует сервис синхронизации ежедневной памяти с LLM.
    *   **Покрытие**: `src/memory_layer/services/memory_sync_llm_service.py` в контексте ежедневной памяти.
*   **`test_memory_profile_runtime_integration.py`**:
    *   **Назначение**: Тестирует интеграцию профиля памяти LLM с рантаймом.
    *   **Покрытие**: Взаимодействие между `src/llm/profiles/memory_profile.py` и `src/runtime_agents/memory_agent/`.
*   **`test_memory_profile_typed_contour.py`**:
    *   **Назначение**: Проверяет типизированный контур профиля памяти.
    *   **Покрытие**: Типизация и структура `src/llm/profiles/memory_profile.py`.
*   **`test_memory_request_factory_split_contract.py`**:
    *   **Назначение**: Тестирует разделение контракта фабрики запросов для памяти.
    *   **Покрытие**: `src/runtime_agents/memory_agent/memory_request_factory.py` и связанные контракты.
*   **`test_memory_run_ledger_contract.py`**:
    *   **Назначение**: Проверяет контракт для журнала запусков памяти.
    *   **Покрытие**: `src/memory_layer/domain/memory_run_ledger.py` и `src/memory_layer/run_ledger_repository.py`.
*   **`test_memory_sync_persistence_service.py`**:
    *   **Назначение**: Тестирует сервис синхронизации сохранения памяти.
    *   **Покрытие**: `src/memory_layer/services/memory_sync_persistence_service.py`.
*   **`test_memory_sync_port_split_sequence.py`**:
    *   **Назначение**: Тестирует разделенную последовательность порта синхронизации памяти.
    *   **Покрытие**: `src/memory_layer/services/memory_sync_port.py`.
*   **`test_primary_agent_prompt_config.py`**:
    *   **Назначение**: Тестирует конфигурацию промптов для основного агента.
    *   **Покрытие**: `src/adk_agents/primary_agent/prompt_config.py`.
*   **`test_profile_interface.py`**:
    *   **Назначение**: Тестирует общий интерфейс профилей LLM.
    *   **Покрытие**: Базовые контракты для профилей в `src/llm/profiles/contracts.py`.
*   **`test_profile_registry.py`**:
    *   **Назначение**: Тестирует реестр профилей LLM.
    *   **Покрытие**: `src/llm/profiles/registry.py`.
*   **`test_provider_routing.py`**:
    *   **Назначение**: Тестирует логику маршрутизации запросов к различным провайдерам LLM.
    *   **Покрытие**: `src/llm/provider_routing.py`.
*   **`test_pubsub_oidc_auth.py`**:
    *   **Назначение**: Тестирует аутентификацию OIDC для обработчиков Pub/Sub.
    *   **Покрытие**: Политики безопасности в `src/entrypoints/policies.py` и логика аутентификации для маршрутов Pub/Sub.
*   **`test_pytest_plugin_contract.py`**:
    *   **Назначение**: Тестирует контракт плагина pytest.
    *   **Покрытие**: Инфраструктура pytest, возможно, `conftest.py` или кастомные плагины.
*   **`test_rate_limiter.py`**:
    *   **Назначение**: Общие тесты для базовой функциональности лимитера запросов.
    *   **Покрытие**: `src/services/rate_limit/inmemory_rate_limiter.py` или базовые интерфейсы.
*   **`test_read_firestore_script.py`**:
    *   **Назначение**: Тестирует скрипт для чтения данных из Firestore.
    *   **Покрытие**: `scripts/read_firestore.py` и его взаимодействие с Firestore.
*   **`test_reply_baseline_golden.py`**:
    *   **Назначение**: Тесты для базового "золотого" стандарта ответов, вероятно, сравнивая с заранее определенными ожидаемыми ответами.
    *   **Покрытие**: Логика генерации ответов в `src/llm/llm_service.py` и `src/llm/profiles/reply_profile.py`.
*   **`test_reply_profile_runtime_integration.py`**:
    *   **Назначение**: Тестирует интеграцию профиля ответов LLM с рантаймом.
    *   **Покрытие**: Взаимодействие между `src/llm/profiles/reply_profile.py` и основными агентами.
*   **`test_runtime_dependencies_container.py`**:
    *   **Назначение**: Тестирует контейнер зависимостей времени выполнения.
    *   **Покрытие**: `src/entrypoints/runtime_dependencies.py` и логика внедрения зависимостей.
*   **`test_runtime_security.py`**:
    *   **Назначение**: Тестирует различные аспекты безопасности во время выполнения приложения.
    *   **Покрытие**: Общие механизмы безопасности, аутентификации, авторизации в `src/entrypoints/policies.py` и `src/services/runtime/`.
*   **`test_semantic_gate.py`**:
    *   **Назначение**: Тестирует "семантический шлюз", который, вероятно, выполняет семантическую валидацию или фильтрацию сообщений/действий.
    *   **Покрытие**: Компоненты, реализующие семантическую логику в `src/domain/agent_output/agent_semantic_payload_validator.py` или `src/services/inbound/`.
*   **`test_send_reply_use_case.py`**:
    *   **Назначение**: Тестирует сценарий использования для отправки ответа пользователю.
    *   **Покрытие**: Логика отправки ответов в `src/services/dialog/dialog_service.py` или связанный use case.
*   **`test_settings.py`**:
    *   **Назначение**: Тестирует загрузку и корректность конфигурационных настроек.
    *   **Покрытие**: `src/settings.py`.
*   **`test_source_context_agent_intent.py`**:
    *   **Назначение**: Тестирует намерение агента на основе исходного контекста.
    *   **Покрытие**: Логика определения намерений агента, возможно, в `src/adk_agents/primary_agent/` или `src/domain/`.
*   **`test_source_context_validation_use_cases.py`**:
    *   **Назначение**: Тестирует сценарии использования для валидации исходного контекста.
    *   **Покрытие**: `src/domain/context_validation.py` и связанные use cases.
*   **`test_step5_idempotency.py`**:
    *   **Назначение**: Тестирует идемпотентность на шаге 5 какого-либо пайплайна.
    *   **Покрытие**: `src/services/runtime/step_idempotency.py` и конкретный шаг 5.
*   **`test_structured_extractor.py`**:
    *   **Назначение**: Тестирует сервис для извлечения структурированных данных из LLM-ответов.
    *   **Покрытие**: `src/llm/transport/structured_extractor.py`.
*   **`test_summary_store_daily_idempotency.py`**:
    *   **Назначение**: Тестирует идемпотентность ежедневного хранилища сводок.
    *   **Покрытие**: `src/memory_layer/services/memory_summary_service.py` и логика ежедневных сводок.
*   **`test_summary_store_rolling_migration.py`**:
    *   **Назначение**: Тестирует миграцию хранилища "скользящих" сводок.
    *   **Покрытие**: Логика миграции в `src/memory_layer/services/memory_summary_service.py` или связанных use cases.
*   **`test_summary_store_rolling_semantics.py`**:
    *   **Назначение**: Тестирует семантику "скользящих" сводок хранилища.
    *   **Покрытие**: `src/memory_layer/domain/rolling_content_policy.py` и `src/memory_layer/services/memory_summary_service.py`.
*   **`test_telegram_rate_limiter.py`**:
    *   **Назначение**: Тестирует лимитер запросов, специфичный для Telegram.
    *   **Покрытие**: `src/services/rate_limit/` в контексте Telegram-адаптеров.
*   **`test_timezone_foundation.py`**:
    *   **Назначение**: Тестирует базовую функциональность часовых поясов.
    *   **Покрытие**: `src/services/timezone/` и `src/domain/`.
*   **`test_transport_core_neutrality.py`**:
    *   **Назначение**: Проверяет нейтральность транспортного ядра, то есть его независимость от конкретных LLM-провайдеров.
    *   **Покрытие**: `src/llm/transport/executor.py` и `src/llm/llm_base_contracts.py`.
*   **`test_vertex_parser.py`**:
    *   **Назначение**: Тестирует парсер ответов Vertex AI.
    *   **Покрытие**: `src/llm/vertex/vertex_parser.py`.
*   **`test_vertex_provider.py`**:
    *   **Назначение**: Тестирует провайдер LLM для Google Cloud Vertex AI.
    *   **Покрытие**: `src/llm/vertex/vertex_provider.py`.
*   **`architecture/`**:
    *   **Назначение**: Содержит тесты, проверяющие архитектурные правила и зависимости в проекте. Это может быть статический анализ кода для выявления циклических зависимостей или нарушений слоев.
    *   **Покрытие**: Архитектурные правила, определенные в `scripts/check_architecture.py` и общая структура проекта `src/`.
