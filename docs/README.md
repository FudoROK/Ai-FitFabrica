# AI FitFabrica Documentation Index

Дата актуализации: 2026-06-17

Эта папка содержит canonical-документацию проекта. Если документ противоречит коду, приоритет имеет код и актуальные тесты, но именно эти файлы являются стартовой точкой для Codex, разработчика или инвестора.

## Главные документы

1. [00_PROJECT_MASTER_PLAN.md](00_PROJECT_MASTER_PLAN.md) - общий план реализации, что уже сделано, что осталось, текущий статус продукта.
2. [01_ACTION_LOG_CHECKLIST.md](01_ACTION_LOG_CHECKLIST.md) - журнал действий и чеклист этапов, чтобы новая сессия видела ход работ.
3. [02_TECHNICAL_PROJECT_MAP.md](02_TECHNICAL_PROJECT_MAP.md) - техническое описание проекта, дерево папок и ответственность ключевых файлов.
4. [03_AGENT_SYSTEM_GUIDE.md](03_AGENT_SYSTEM_GUIDE.md) - единый документ по агентам, контрактам, взаимодействию с backend и рекомендациям по моделям.
5. [04_OWNER_REMAINING_WORK.md](04_OWNER_REMAINING_WORK.md) - короткий документ для владельца проекта: что осталось сделать и в каком порядке.

## Финансы и investor materials

- [costs/workflow_agent_cost_map_v1.md](costs/workflow_agent_cost_map_v1.md) - карта себестоимости workflow и агентов.
- [costs/credits_policy_v1.md](costs/credits_policy_v1.md) - правила списания credits.
- [costs/credits_pricing_table_v1.md](costs/credits_pricing_table_v1.md) - pricing baseline.
- [../output/pdf/ai_fitfabrica_investor_unit_economics_ru.pdf](../output/pdf/ai_fitfabrica_investor_unit_economics_ru.pdf) - PDF для инвесторов по экономике, затратам и марже.

## Supporting documents

- [current_system_full_documentation.md](current_system_full_documentation.md) - расширенная техническая справка текущего состояния.
- [tests_description.md](tests_description.md) - что покрывают тесты и какие проверки считаются базовыми.
- [runbooks/deploy_backend_and_frontend_ru.md](runbooks/deploy_backend_and_frontend_ru.md) - команды деплоя backend/frontend.
- [reports/](reports/) - acceptance/review reports.
- [reports/2026-06-17-try-on-local-readiness-report.md](reports/2026-06-17-try-on-local-readiness-report.md) - readiness report перед VM/staging live acceptance для Try-On цепочки.
- [superpowers/](superpowers/) - исторические specs/plans. Они полезны для traceability, но не являются главным источником истины после появления canonical-документов выше.

## Documentation rules

- Новые важные решения сначала добавлять в `01_ACTION_LOG_CHECKLIST.md`.
- Если меняется архитектура, обновлять `00_PROJECT_MASTER_PLAN.md`, `02_TECHNICAL_PROJECT_MAP.md` и при необходимости `03_AGENT_SYSTEM_GUIDE.md`.
- Если меняется economics/pricing, обновлять `docs/costs/*` и investor PDF.
- Старые промежуточные документы не удалять без проверки тестов и ссылок; переносить в `docs/archive/`.
