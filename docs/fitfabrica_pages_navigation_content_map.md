# AI FitFabrica Pages, Navigation and Content Map

## 1. Purpose of This Document

This document describes the current website structure implemented in `apps/web`:

- all pages
- route map
- where the main buttons lead
- what each page communicates
- what text role each page plays in the product narrative

The document reflects the current frontend implementation state.

## 2. Site Structure Overview

The site is split into two main contours:

- Public website
- Workspace

Public website is for product presentation, routing users into the correct scenario, and collecting sign-in or demo intent.

Workspace is for product workflows:

- try-on
- outfit building
- similar-item search
- product card generation
- content package workflows
- profile and balance sections

## 3. Full Route Map

### Public pages

- `/` — Главная
- `/for-you` — Для себя
- `/business` — Для бизнеса
- `/capabilities` — Возможности
- `/how-it-works` — Как работает
- `/pricing` — Тарифы
- `/privacy` — Безопасность
- `/contacts` — Контакты / Запросить демо
- `/sign-in` — Вход

### Workspace pages

- `/workspace` — Кабинет
- `/workspace/try-on/new` — Новая примерка
- `/workspace/try-on/result` — Результат примерки
- `/workspace/outfit-builder` — Подбор образа
- `/workspace/similar` — Найти похожее
- `/workspace/product-card` — Карточка товара
- `/workspace/content-package` — Контент-пакет
- `/workspace/style-profile` — Профиль стиля
- `/workspace/business-profile` — Профиль бизнеса
- `/workspace/credits` — Кредиты и баланс
- `/workspace/history` — История и проекты

## 4. Public Header Navigation

Current top navigation:

- `Главная` → `/`
- `Для себя` → `/for-you`
- `Для бизнеса` → `/business`
- `Возможности` → `/capabilities`
- `Как работает` → `/how-it-works`
- `Тарифы` → `/pricing`

Header action buttons:

- `Войти` → `/sign-in`
- `Начать примерку` → `/workspace/try-on/new`

Notes:

- `Безопасность` and `Контакты` were removed from the top navigation
- these routes remain available through the footer and direct links

## 5. Footer Navigation

Current footer links:

- `Безопасность` → `/privacy`
- `Тарифы` → `/pricing`
- `Контакты` → `/contacts`

## 6. Workspace Sidebar Navigation

Workspace sidebar routes:

- `Кабинет` → `/workspace`
- `Новая примерка` → `/workspace/try-on/new`
- `Результат примерки` → `/workspace/try-on/result`
- `Подбор образа` → `/workspace/outfit-builder`
- `Найти похожее` → `/workspace/similar`
- `Карточка товара` → `/workspace/product-card`
- `Контент-пакет` → `/workspace/content-package`
- `Профиль стиля` → `/workspace/style-profile`
- `Профиль бизнеса` → `/workspace/business-profile`
- `Кредиты` → `/workspace/credits`
- `История` → `/workspace/history`

## 7. Page-by-Page Description

### 7.1 Главная `/`

#### Purpose

The homepage introduces AI FitFabrica as one unified product for:

- virtual try-on
- content generation
- fashion workflows

#### Main message

The page says that the product combines fitting, content production and operational scenarios in one structured interface.

#### Main text blocks

- Hero:
  - AI-команда для одежды
  - Примерка, контент и fashion workflow в одном продукте.
- Route split:
  - Два понятных контура
- Capabilities:
  - Что уже заложено в сайт
- Process:
  - Frontend объясняет процесс, но не тащит бизнес-логику на себя
- Final CTA:
  - Структура собрана под production-контур

#### Main buttons

- `Для себя` → `/for-you`
- `Для бизнеса` → `/business`
- `Открыть workspace` → `/workspace`
- `Запросить демо` → `/contacts`

### 7.2 Для себя `/for-you`

#### Purpose

Explains the personal use scenario.

#### Main message

The page positions the product as a tool to check if a garment fits before purchase and to reduce unnecessary buying mistakes.

#### Main text blocks

- Hero:
  - Проверяйте вещи до покупки, а не после доставки
- Feature section:
  - Основные действия

#### Main buttons

- `Начать примерку` → `/workspace/try-on/new`

#### Content meaning

The page communicates:

- try-on by photo
- styling support
- silhouette and color checks
- similar item comparison in another budget

### 7.3 Для бизнеса `/business`

#### Purpose

Explains the B2B value proposition.

#### Main message

The page presents AI FitFabrica as a business workflow product for content, catalog production and team operations.

#### Main text blocks

- Hero:
  - Каталог, маркетплейс и контент без хаоса в процессах
- Feature section:
  - Что получает команда

#### Main buttons

- `Запросить демо` → `/contacts`

#### Content meaning

The page communicates:

- product card generation
- content packages
- virtual models
- repeatable team workflows

### 7.4 Возможности `/capabilities`

#### Purpose

Shows the product capability inventory.

#### Main message

The page explains that the product is built from modular workflows rather than isolated prototype screens.

#### Main text block

- Product-модули, а не набор разрозненных экранов

#### Content meaning

The page lists the currently represented capability groups:

- try-on
- outfit building
- similar-item search
- product card generation
- content packages
- quality control

### 7.5 Как работает `/how-it-works`

#### Purpose

Explains the backend-first workflow logic.

#### Main message

The page makes it clear that the frontend collects, explains and displays state, while the backend executes workflow logic.

#### Main text block

- Как устроен поток работы

#### Content meaning

The page walks through:

- upload
- validation
- generation
- result delivery

### 7.6 Тарифы `/pricing`

#### Purpose

Presents the tariff structure.

#### Main message

The page frames pricing as a product structure prepared for backend billing rather than hardcoded subscription logic.

#### Main text block

- Структура тарифов для дальнейшего backend billing

#### Plans shown

- `Start`
- `Studio`
- `Enterprise`

#### Main buttons

Each plan contains:

- `Обсудить подключение` → `/contacts`

### 7.7 Безопасность `/privacy`

#### Purpose

Explains privacy and security posture.

#### Main message

The page communicates architectural discipline:

- no secrets in frontend
- typed DTO and validation readiness
- route separation for access control growth

#### Main text block

- Спокойная прозрачность вместо маркетингового шума

### 7.8 Контакты `/contacts`

#### Purpose

Collects business demo requests.

#### Main message

The page is for demo, integration discussion and use-case intake.

#### Main text block

- Запросить демо и обсудить интеграцию

#### Main form fields

- Компания
- Имя и роль
- Email
- Сайт
- Сценарий использования

#### Main button

- `Запросить демо` → form submit on same page

#### Form behavior

Currently the form is connected to a typed frontend integration contract and returns a placeholder integration-ready message.

### 7.9 Вход `/sign-in`

#### Purpose

Collects sign-in intent.

#### Main message

The page prepares the sign-in flow for future backend integration with magic link or SSO.

#### Main text block

- Войти в рабочее пространство

#### Main form fields

- Рабочий email
- Пространство:
  - Личный контур
  - Бизнес-контур

#### Main button

- `Получить ссылку` → form submit on same page

## 8. Workspace Page Descriptions

### 8.1 Кабинет `/workspace`

#### Purpose

Main workspace entry page.

#### Main message

Shows where the user should go next and presents workspace as a structured product area rather than a dashboard full of random widgets.

#### Main buttons

- `Новая примерка` → `/workspace/try-on/new`
- `История` → `/workspace/history`

### 8.2 Новая примерка `/workspace/try-on/new`

#### Purpose

Entry point for the try-on workflow.

#### Main message

The page separates:

- person photo input
- garment photo input
- preview canvas
- AI status panel

#### Main buttons

- `Сгенерировать примерку` → disabled for now
- `Открыть результат` → `/workspace/try-on/result`

#### Content meaning

The page already communicates:

- upload expectations
- future backend validation role
- quality and proportion check pipeline

### 8.3 Результат примерки `/workspace/try-on/result`

#### Purpose

Shows what the result stage of try-on looks like.

#### Main message

The page focuses on one visual result plus quality confirmation and next actions.

#### Main buttons

- `Продолжить в подбор образа` → `/workspace/outfit-builder`
- `Сохранить в историю` → `/workspace/history`

### 8.4 Подбор образа `/workspace/outfit-builder`

#### Purpose

Shows the outfit-building workflow.

#### Main message

The page explains that this route is intended for briefs, lookboards and recommendation output.

#### Content meaning

The page currently communicates:

- scenario brief
- constraints
- result output area

### 8.5 Найти похожее `/workspace/similar`

#### Purpose

Search route for similar but cheaper alternatives.

#### Main message

The page separates source item, match logic and future result blocks.

#### Content meaning

The page is prepared for:

- style match
- color match
- budget match
- next-step actions

### 8.6 Карточка товара `/workspace/product-card`

#### Purpose

Product card generation workflow.

#### Main message

The page frames the route as a process from source material to commercial-ready product card.

#### Content meaning

It communicates:

- source photos and attributes
- brand tone
- target channel
- final DTO for backend generation

### 8.7 Контент-пакет `/workspace/content-package`

#### Purpose

Content package result route.

#### Main message

The page explains that generated content can be grouped into ready-to-use marketing and marketplace outputs.

#### Content meaning

It currently describes:

- creative formats
- descriptions and e-commerce labels
- export readiness

### 8.8 Профиль стиля `/workspace/style-profile`

#### Purpose

Style profile route for personal preferences.

#### Main message

The page is intended to store structured user style preferences for later workflow use.

#### Content meaning

The page currently represents:

- silhouettes
- color palette
- categories and restrictions
- history of style decisions

### 8.9 Профиль бизнеса `/workspace/business-profile`

#### Purpose

Business profile route for company settings and brand context.

#### Main message

The page is the place for structured business context rather than mixing such settings into random workflow pages.

#### Content meaning

The page currently represents:

- brand tone
- target channels
- product categories
- result policy

### 8.10 Кредиты и баланс `/workspace/credits`

#### Purpose

Balance and credits route.

#### Main message

The page reserves a dedicated space for credits without implementing billing logic in the frontend.

#### Content meaning

The route is prepared for:

- balance
- packages
- charge policy

### 8.11 История и проекты `/workspace/history`

#### Purpose

History and project archive route.

#### Main message

The page provides a dedicated location for completed workflows and currently shows an honest empty state.

#### Content meaning

After backend integration this page is intended to contain:

- saved workflows
- task statuses
- generated results

## 9. Main Button Map

### From public pages

- `Войти` → `/sign-in`
- `Начать примерку` → `/workspace/try-on/new`
- `Для себя` → `/for-you`
- `Для бизнеса` → `/business`
- `Открыть workspace` → `/workspace`
- `Запросить демо` → `/contacts`
- `Обсудить подключение` → `/contacts`

### From workspace

- `Новая примерка` → `/workspace/try-on/new`
- `История` → `/workspace/history`
- `Открыть результат` → `/workspace/try-on/result`
- `Продолжить в подбор образа` → `/workspace/outfit-builder`
- `Сохранить в историю` → `/workspace/history`

### Buttons without route transition

- `Запросить демо` on `/contacts` submits the form on the same page
- `Получить ссылку` on `/sign-in` submits the form on the same page
- `Сгенерировать примерку` on `/workspace/try-on/new` is currently disabled until backend workflow integration

## 10. Text Role of the Whole Site

The current text system does three things:

- explains what AI FitFabrica is
- separates B2C and B2B user intent clearly
- shows that the product is built around structured workflows, not around decorative AI marketing

The copy style is:

- calm
- direct
- product-led
- operational

It avoids:

- hype-heavy AI language
- fake promises
- abstract startup wording
- frontend pretending to execute backend logic

## 11. Documentation Status

This document reflects the current implementation as of the present frontend state in `apps/web`.

If routes, page sections, CTA labels or workflow priorities change, this file should be updated together with the UI.
