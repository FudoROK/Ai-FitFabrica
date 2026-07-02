# Стратегия источников для Similar Search

## Цель

Similar Search не должен зависеть от скрытого парсинга чужих маркетплейсов. Базовая стратегия:

1. искать в нашей локальной базе одобренных товаров;
2. подключать бизнес-клиентов через их seller API, фиды или ручную загрузку;
3. использовать партнёрские фиды и официальные API;
4. использовать открытый web/search discovery только как источник кандидатов, если это не нарушает правила источника;
5. не использовать hidden scraping, browser automation, обход капч, обход логинов и массовый неразрешённый парсинг.

## Типы источников

| Source type | Что означает | Когда можно использовать |
| --- | --- | --- |
| `local_catalog` | Наша база одобренных товаров | Уже используется |
| `official_api` | Официальный API площадки | После получения доступа и договора/ключей |
| `partner_feed` | CSV/XML/YML/API-фид партнёра | После разрешения партнёра |
| `seller_connected_store` | Магазин бизнес-клиента через seller API/OAuth | Когда продавец сам подключил доступ |
| `admin_verified_link` | Ссылка, вручную проверенная админом | Для точечных источников и MVP |
| `instagram_business` | Instagram Business / Graph API | После настройки Meta permissions |
| `instagram_public_discovery` | Instagram-ссылки/посты, найденные через разрешённый web/search discovery | Только как кандидаты, не как готовые товары |
| `public_web_allowed` | Открытая web-страница, которую разрешено индексировать/использовать | Только если источник разрешает такое использование |
| `search_engine_discovery` | Поиск кандидатов через поисковую систему/API | Только через официальный search API и с соблюдением правил |

## Что важно

- Seller API не равен поиску по всему маркетплейсу. Он даёт доступ только к товарам конкретного продавца.
- Search engine discovery не должен автоматически превращаться в наш каталог. Такие результаты нужно помечать как кандидаты.
- Instagram public discovery не является полноценным marketplace API. Такой результат обычно не имеет гарантированной цены, остатка, доставки и должен идти как `candidate`, а не как `offer`.
- В production показывать пользователю лучше проверенные источники: локальная база, partner feeds, seller-connected stores.
- Web/search discovery должен быть ограничен лимитами, кэшем, source trust score и явной маркировкой источника.

## Следующий технический шаг

Текущий backend уже содержит safe-заглушку search engine discovery. Она умеет формировать site-scoped Instagram-запросы вида `site:instagram.com ...`, но не делает live-вызовы, пока не настроен официальный search API, лимиты и правила использования.

Также подготовлен mapper для будущего search API:

- вход: `SearchEngineResult` (`provider`, `rank`, `title`, `url`, `snippet`);
- фильтр: пропускаются только настоящие `instagram.com` / `*.instagram.com` URL;
- выход: `MarketplaceDiscoveryCandidate`;
- lookalike-домены вроде `instagram.com.evil.example` отклоняются;
- candidate остаётся review-required и не становится товаром автоматически.

Следующий технический шаг: добавить feature-flagged live adapter для конкретного официального search API. Adapter должен возвращать только `candidate` записи, не обходить капчи/логины и не превращать найденные страницы в нормальные товары без проверки.

## Настройки live discovery

Live-вызовы поисковой системы выключены по умолчанию.

Env-поля:

- `ENABLE_SEARCH_ENGINE_DISCOVERY=false`
- `SEARCH_ENGINE_DISCOVERY_PROVIDER=disabled`
- `SEARCH_ENGINE_DISCOVERY_DAILY_LIMIT=0`
- `SEARCH_ENGINE_DISCOVERY_API_KEY`

Включать live discovery можно только после выбора официального search API, настройки лимитов и проверки правил использования.

Runtime registry уже читает эти значения через factory-контур. Если discovery выключен, нет ключа или provider неизвестен, backend возвращает безопасный `skipped` report и не делает live-вызовы.

## Admin review для candidates

Открытые Instagram/web/search результаты не становятся товарами автоматически. Они должны пройти admin review:

- `GET /api/admin/business-catalog/discovery-candidates/pending`
- `POST /api/admin/business-catalog/discovery-candidates/{candidate_id}/approve`
- `POST /api/admin/business-catalog/discovery-candidates/{candidate_id}/reject`

Текущий foundation использует backend service boundary и in-memory repository для локального/runtime placeholder. Перед production-включением live discovery нужен SQL repository и миграция для durable candidate review.
