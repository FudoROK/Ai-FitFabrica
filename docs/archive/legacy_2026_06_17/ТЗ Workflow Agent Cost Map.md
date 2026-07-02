# ТЗ: Workflow Agent Cost Map v1 и расчёт внутренней валюты AI FitFabrica

## Цель

Сделать карту работы агентов AI FitFabrica по основным workflows и рассчитать примерную себестоимость каждого действия пользователя.

Нужно понять:

* какие агенты вызываются в каждом workflow;
* какие модели Gemini используются;
* сколько вызовов происходит;
* где есть image/vision/generation шаги;
* где возможны retry/repair;
* сколько стоит один успешный workflow;
* сколько стоит неуспешный workflow;
* сколько нужно брать с пользователя во внутренней валюте;
* какая должна быть маржа.

Важно: сейчас **не проектируем локальных агентов**.
Все агенты считаются cloud/Gemini, как в текущем плане проекта.

---

## 1. Workflows, которые нужно покрыть

Сделать cost map минимум для следующих workflows:

### 1. B2C Try-On Workflow

Пользователь загружает фото человека и фото одежды.

Шаги:

1. Human Identity Agent
2. Human Identity backend suitability policy
3. Garment Identity Agent
4. Material / Texture Agent, если включён в workflow
5. Try-On Instruction Agent
6. Try-On image generation / virtual try-on provider call
7. Quality Verifier Agent
8. Repair Agent, если результат repairable
9. Повторный Quality Verifier после repair
10. Fashion Stylist Agent, если включён совет стилиста
11. Backend сохраняет результат и списывает credits

Нужно посчитать:

* cost без repair;
* cost с одним repair;
* cost с retry;
* cost если Human Identity заблокировал фото;
* cost если Garment Identity failed;
* cost если generation failed;
* cost если Quality Verifier failed.

---

### 2. B2B Product Card Workflow

Пользователь загружает фото товара и параметры карточки.

Шаги:

1. Garment Identity Agent
2. Material / Texture Agent, если используется
3. Product Card Agent
4. Pricing Agent, если включён price recommendation
5. Product image / model photo generation, если создаётся фото на модели
6. Quality Verifier Agent
7. Repair Agent, если нужно
8. Content/export assembly
9. Backend сохраняет product_card, artifacts, ledger

Нужно посчитать:

* product card text-only;
* product card with generated model photo;
* product card with content package;
* product card with repair;
* failed before generation;
* failed after generation.

---

### 3. Similar / Cheaper Product Workflow

Пользователь загружает фото товара или ссылку.

Шаги:

1. Если фото — Garment Identity Agent
2. Если ссылка — Reference Parser / Product Extractor
3. Search query builder
4. Marketplace Search / external product search
5. Pricing Agent
6. Marketplace Agent
7. Backend ranking
8. Backend сохраняет offers и search result

Нужно посчитать:

* поиск по фото;
* поиск по ссылке;
* поиск с marketplace API;
* поиск без найденных результатов;
* повторный поиск / расширение поиска.

---

### 4. Outfit Recommendation Workflow

Пользователь загружает вещь и хочет собрать образ.

Шаги:

1. Garment Identity Agent
2. User Profile Agent
3. Fashion Stylist Agent
4. Trend Agent, если включены тренды
5. Marketplace Agent, если нужны реальные товары
6. Pricing Agent, если есть бюджет
7. Backend сохраняет outfit result

Нужно посчитать:

* образ без поиска товаров;
* образ с поиском товаров;
* образ с trend analysis;
* несколько вариантов образов.

---

### 5. B2B Pricing Workflow

Пользователь хочет понять цену товара.

Шаги:

1. Garment Identity Agent или reuse saved garment analysis
2. Marketplace Agent / competitor search
3. Pricing backend calculation
4. Pricing Agent explanation
5. Backend сохраняет pricing report

Нужно посчитать:

* pricing по уже сохранённому анализу;
* pricing с новым анализом фото;
* pricing с marketplace search;
* pricing без marketplace search.

---

### 6. Content Package Workflow

Пользователь хочет получить пакет контента для товара.

Шаги:

1. Product Card / saved garment analysis
2. Business Profile Agent
3. Product Card Agent для разных каналов
4. Fashion Stylist Agent, если нужен стиль подачи
5. Pricing Agent, если нужен price positioning
6. Image generation, если создаются новые visual assets
7. Quality Verifier Agent для каждого visual
8. Export service
9. Backend сохраняет content package

Нужно посчитать:

* text-only package;
* package with 1 generated image;
* package with multiple images;
* package with repair;
* package with export ZIP.

---

## 2. Сделать таблицу Workflow Agent Cost Map

Создать документ:

```text
docs/costs/workflow_agent_cost_map_v1.md
```

В документе должна быть таблица по каждому workflow.

Поля таблицы:

```text
workflow_type
step_order
step_name
agent_name
provider
model
input_type
output_type
required
can_retry
can_repair
charged_to_user
free_if_failed
expected_input_tokens
expected_output_tokens
expected_image_inputs
expected_image_outputs
expected_provider_cost_usd
expected_internal_cost_usd
notes
```

Пример строки:

```text
try_on
1
human_identity_analysis
human_identity_agent
gemini
gemini-2.5-flash
image+text
json
yes
yes
no
no_if_blocked
yes
...
```

---

## 3. Сделать price config

Не хардкодить цены внутри workflow.

Создать конфиг:

```text
src/costs/provider_price_config.py
```

или другой подходящий config/module по текущей архитектуре.

В price config должны быть:

```text
provider
model
input_text_price_per_1m_tokens_usd
output_text_price_per_1m_tokens_usd
image_input_price_unit
image_output_price_unit
image_generation_price_unit
currency
effective_date
source_note
```

Первичные значения взять из официальной Gemini / Google pricing страницы на дату реализации.

Важно:

* указать дату, когда цены были внесены;
* указать источник в комментарии;
* не смешивать provider tokens и нашу внутреннюю валюту;
* сделать возможность быстро обновить цены без изменения workflow code.

---

## 4. Расчёт себестоимости agent invocation

Для каждого вызова агента нужно сохранять cost metadata.

Проверить текущий `AgentInvocationService` и ledger. Если нужных полей нет — добавить.

Нужные поля:

```text
job_id
workflow_type
agent_name
provider
model
input_tokens
output_tokens
image_input_count
image_output_count
generation_output_count
attempt_number
retry_reason
repair_reason
latency_ms
validation_status
estimated_provider_cost_usd
estimated_internal_cost_usd
cost_config_version
```

Если provider не возвращает точные token usage, сделать fallback estimate:

```text
estimated_input_tokens
estimated_output_tokens
estimated_image_count
```

Но в отчёте обязательно помечать:

```text
usage_source = provider_reported | estimated
```

---

## 5. Расчёт себестоимости workflow

Для каждого job/workflow нужно уметь получить summary:

```text
job_id
workflow_type
status
total_agent_calls
total_generation_calls
total_retry_count
total_repair_count
direct_provider_cost_usd
retry_cost_usd
repair_cost_usd
storage_estimated_cost_usd
total_internal_cost_usd
credits_charged
revenue_estimated_usd
gross_margin_usd
gross_margin_percent
```

Сделать отдельный service:

```text
WorkflowCostEstimator
```

или аналогичный модуль по архитектуре проекта.

Он должен уметь считать:

```text
estimate_before_run
actual_after_run
failed_job_cost
successful_job_cost
repair_cost
retry_cost
```

---

## 6. Правила списания credits

Сделать документ:

```text
docs/costs/credits_policy_v1.md
```

В нём описать правила:

### Не списывать credits

```text
Human Identity blocked unsuitable photo
Garment Identity failed before generation
provider/system error
contract validation failed
backend policy rejected input
```

### Списывать credits

```text
successful Try-On
successful Product Card
successful Similar Search
successful Outfit Recommendation
successful Pricing Report
successful Content Package
user-requested extra variant
user-requested regeneration
```

### Бесплатно для пользователя

```text
repair из-за нашей quality failure
retry из-за provider/system failure
повторный Quality Verifier после нашего repair
```

### Платно для пользователя

```text
дополнительный вариант по запросу пользователя
новая генерация из-за изменения input
новый поиск дешевле/похожего
расширенный content package
```

---

## 7. Внутренняя валюта

Нужно предложить внутреннюю валюту проекта.

Рабочее название:

```text
FitFabrica Credits
```

или коротко:

```text
credits
```

Важно: не называть её model tokens, чтобы не путать с LLM tokens.

Нужно предложить курс:

```text
1 credit = X KZT
```

и обосновать через себестоимость workflows.

Нужно рассчитать минимум 3 варианта:

### Conservative

Высокая маржа, запас на repair/retry.

```text
target_margin_multiplier = 5x
```

### Balanced

Рабочая цена для старта.

```text
target_margin_multiplier = 3x
```

### Aggressive

Низкая цена для привлечения пользователей.

```text
target_margin_multiplier = 2x
```

Для каждого workflow дать рекомендуемую цену в credits:

```text
try_on_basic
try_on_with_style_advice
product_card_text_only
product_card_with_model_photo
similar_search
outfit_recommendation
pricing_report
content_package_basic
content_package_with_images
```

---

## 8. Предварительная pricing table

Создать документ:

```text
docs/costs/credits_pricing_table_v1.md
```

Таблица должна иметь поля:

```text
product_action
workflow_type
direct_cost_usd_min
direct_cost_usd_avg
direct_cost_usd_max
internal_cost_kzt_avg
recommended_credits_conservative
recommended_credits_balanced
recommended_credits_aggressive
user_price_kzt
expected_margin_percent
notes
```

Пример действий:

```text
B2C Try-On Basic
B2C Try-On + Stylist Advice
B2C Extra Try-On Variant
B2B Product Card Text Only
B2B Product Card + Model Photo
B2B Product Card + Content Package
Similar Product Search
Cheaper Product Search
Outfit Recommendation
Pricing Report
```

---

## 9. CLI report

Сделать CLI script:

```text
scripts/report_workflow_costs.py
```

Команды:

```bash
python scripts/report_workflow_costs.py --since 2026-06-01
python scripts/report_workflow_costs.py --workflow try_on
python scripts/report_workflow_costs.py --workflow product_card
python scripts/report_workflow_costs.py --format markdown
python scripts/report_workflow_costs.py --format json
```

Report должен показывать:

```text
total_jobs
successful_jobs
failed_jobs
avg_cost_usd
avg_cost_kzt
avg_credits_charged
avg_margin
most_expensive_agent
retry_cost_total
repair_cost_total
free_failed_job_cost_total
provider_cost_by_agent
provider_cost_by_model
```

---

## 10. Admin/API endpoint

Если быстро и безопасно — добавить admin-only endpoint:

```text
GET /api/admin/costs/workflow-summary
GET /api/admin/costs/jobs/{job_id}
```

Если admin auth ещё не готов — не открывать public endpoint.
Тогда пока достаточно CLI report.

---

## 11. Tests

Добавить tests:

```text
tests/test_provider_price_config.py
tests/test_workflow_cost_estimator.py
tests/test_credits_pricing_policy.py
tests/test_workflow_agent_cost_map_contract.py
```

Проверить:

```text
cost считается корректно;
failed before generation не списывает credits;
repair по нашей ошибке не списывает credits;
user-requested extra variant списывает credits;
нет hardcoded provider prices внутри workflow;
unknown provider/model fail-closed или требует manual price config;
CLI report формируется;
```

Обычные unit tests не должны вызывать реальный Gemini.

---

## 12. Важные ограничения

1. Не менять сейчас provider strategy.
2. Все расчёты делать по текущему Gemini/cloud runtime проекта.
3. Не менять production workflow logic без необходимости.
4. Не списывать реальные credits в тестах.
5. Не хардкодить цены в route/use_case workflow.
6. Все цены provider/model должны лежать в отдельном price config.
7. Все расчёты должны быть reproducible через config version.
8. Все суммы должны быть estimates, если provider не вернул точный usage.
9. В отчётах явно разделять:

   * provider cost;
   * internal cost;
   * charged credits;
   * estimated revenue;
   * margin.
10. Не смешивать LLM tokens, provider usage и внутренние FitFabrica credits.
11. Не менять правила списания credits без отдельного согласования.
12. Не открывать admin cost endpoints публично без admin auth.
13. Unit tests не должны вызывать реальный Gemini.
14. Реальные provider prices должны быть взяты из официального источника и иметь effective date.
15. Если точная цена image generation / virtual try-on неизвестна, указать её как configurable estimate и отдельно отметить в отчёте.

---

## 13. Итоговый результат от Codex

После выполнения дать отчёт:

```text
1. Какие workflows покрыты.
2. Какие агенты входят в каждый workflow.
3. Где основные расходы.
4. Средняя себестоимость каждого workflow.
5. Предложенный курс credits.
6. Предложенная цена действий в credits.
7. Какие поля добавлены в ledger.
8. Какие файлы изменены.
9. Какие тесты добавлены.
10. Команды проверки.
11. Что ещё нужно уточнить для точной экономики.
```

Главный deliverable:

```text
docs/costs/workflow_agent_cost_map_v1.md
docs/costs/credits_policy_v1.md
docs/costs/credits_pricing_table_v1.md
scripts/report_workflow_costs.py
```

Цель этапа — получить первую нормальную экономику AI FitFabrica:

```text
сколько стоит действие
сколько credits брать
какая маржа
где дорогие агенты
где retries/repair съедают деньги
```
