# AI FitFabrica — Project Instructions

Этот файл является проектной инструкцией для разработки AI FitFabrica.

Он дополняет глобальные правила разработки и уточняет только то, что относится к этому проекту.

## 1. Суть проекта

AI FitFabrica — это агентная fashion-commerce платформа.

Это не обычный сайт, не AI-фоторедактор, не витрина моделей и не простая примерочная.

Платформа помогает:

### B2C-пользователям
- примерять одежду на себе;
- понимать, подходит ли вещь;
- подбирать образы;
- искать похожие товары;
- находить варианты дешевле;
- получать рекомендации по стилю, трендам и бюджету.

### B2B-клиентам
- создавать карточки товаров;
- делать фото товара на модели;
- готовить контент для маркетплейсов и Instagram;
- анализировать похожие товары и конкурентов;
- получать рекомендации по цене, карточке и продажам.

Главная формула проекта:

Модели генерируют.  
Агенты работают.  
Backend управляет.

## 2. Главный архитектурный принцип

Frontend и mobile app являются только интерфейсом.

Они не должны содержать:
- бизнес-логику;
- AI workflow;
- orchestration logic;
- credits logic;
- retry / repair logic;
- billing rules;
- marketplace matching logic;
- agent decision logic.

Вся логика выполняется на backend.

Правильная схема:

Site / App  
→ Backend creates job  
→ Backend chooses workflow  
→ Backend calls required agents  
→ Agents return structured outputs  
→ Backend runs generation / search / recommendation tools  
→ Quality Verifier checks result  
→ Backend decides repair / retry / reject / success  
→ Credits logic records cost  
→ Backend saves result  
→ Site / App shows final result

Запрещённая схема:

Site / App  
→ Direct call to AI model  
→ Image / answer shown to user

Так делать нельзя.

## 3. Технологический фокус проекта

Проект строится Google-first.

Основной backend:
- FastAPI;
- Cloud Run;
- Pub/Sub;
- Cloud Tasks;
- Google Cloud Workflows;
- Cloud Storage;
- Firestore;
- Cloud SQL PostgreSQL на старте;
- AlloyDB / AlloyDB Vector позже при росте;
- BigQuery для аналитики, экономики и трендов.

AI / agents:
- Google ADK для кастомных агентов;
- Gemini multimodal для анализа изображений и текста;
- Vertex AI / Gemini / Imagen для generation и image editing;
- Vertex AI Vector Search или AlloyDB Vector для similarity search;
- Vertex AI Search для site / help / document search;
- AI Commerce Search, если проект дойдёт до полноценного product catalog search;
- Model Armor для защиты prompts/responses, если используется в выбранной архитектуре.

Если Google-инструмент не закрывает задачу качества, допускается специализированный внешний tool внутри backend adapter.  
Но управление workflow всё равно остаётся на нашем backend.

## 4. Web frontend

Для сайта и web-кабинета использовать production frontend, а не статический HTML.

Основной web stack:
- Next.js;
- React;
- TypeScript;
- Tailwind CSS;
- component-based architecture.

Запрещено:
- переносить статический HTML как production-код;
- оставлять href="#";
- оставлять кнопки без действия;
- оставлять формы без submit-логики;
- оставлять upload-зоны без загрузки, preview и validation;
- использовать fake AI status;
- хардкодить пользователя, тарифы, balance, credits, историю, AI-результаты;
- держать business logic внутри React components;
- вызывать AI/model provider из browser-кода.

Каждый CTA должен иметь:
- реальный route;
- рабочий action;
- disabled state;
- или feature flag.

## 5. Mobile app

Mobile app является тонким клиентом.

Предпочтительный mobile stack:
- Flutter;
- Dart;
- Firebase SDK;
- Google/Firebase services.

Mobile app должен:
- авторизовать пользователя;
- загружать фото;
- отправлять DTO на backend;
- показывать job status;
- показывать результат;
- показывать ошибки;
- работать с push/status updates, если это нужно.

Mobile app не должен:
- управлять агентами;
- считать credits;
- принимать решение retry / repair;
- напрямую обращаться к AI provider;
- хранить secrets;
- дублировать backend business rules.

## 6. Основные пользовательские маршруты сайта

Public routes:
- `/`
- `/for-you`
- `/business`
- `/features`
- `/pricing`
- `/how-it-works`
- `/about`
- `/contact`
- `/privacy`
- `/login`

Private / workspace routes:
- `/workspace`
- `/workspace/new-fitting`
- `/workspace/similar-search`
- `/workspace/product-card`
- `/workspace/projects`
- `/workspace/credits`
- `/workspace/settings`

Все маршруты должны быть реальными.  
Навигация не должна быть декоративной.

## 7. Основные workflows проекта

### 7.1 B2C Try-On Workflow

Input:
- human photo;
- garment photo or product link;
- user options.

Process:
- create job;
- validate inputs;
- analyze human identity;
- analyze garment identity;
- optionally analyze material / texture;
- run try-on generation;
- verify quality;
- repair or retry if needed;
- generate stylist advice;
- save result;
- return result to user.

User receives:
- final image;
- quality-safe result;
- short style explanation;
- saved history item.

### 7.2 Outfit Recommendation Workflow

Input:
- garment photo / wardrobe item / user style profile / budget.

Process:
- analyze garment;
- read user profile;
- generate outfit options;
- optionally search marketplace alternatives;
- return practical recommendations.

User receives:
- 3–5 outfit options;
- explanation;
- optional shopping suggestions.

### 7.3 Similar / Cheaper Product Workflow

Input:
- garment photo or product link;
- budget;
- marketplace preferences.

Process:
- analyze garment;
- create structured search profile;
- run visual / semantic search;
- query marketplace connectors;
- compare prices;
- filter by budget;
- explain similarity and trade-offs.

User receives:
- similar products;
- cheaper alternatives;
- price comparison;
- recommendation.

### 7.4 B2B Product Card Workflow

Input:
- product photo;
- business profile;
- target platform;
- content package options.

Process:
- analyze garment;
- clean / enhance product visual;
- generate model photo if needed;
- generate title, description, characteristics;
- create marketplace / Instagram content;
- verify quality;
- save product card version.

Business user receives:
- product card;
- images;
- description;
- content package;
- quality notes.

### 7.5 B2B Pricing Workflow

Input:
- product data;
- garment profile;
- marketplace offers;
- competitor data;
- business margin, if available.

Process:
- analyze comparable products;
- calculate market range;
- suggest pricing;
- explain positioning;
- suggest improvements to justify price.

Business user receives:
- recommended price;
- market min / avg / premium range;
- explanation;
- card improvement suggestions.

## 8. Agents

Agents are separate roles with strict input and output contracts.

Agents do not call each other chaotically.

Backend calls agents and controls workflow.

Required agents:

1. Orchestrator Agent  
Understands user task and suggests workflow to backend.

2. User Profile Agent  
Stores and updates B2C style, sizes, budget, preferences and history.

3. Business Profile Agent  
Stores seller profile, brand style, marketplace preferences and content rules.

4. Human Identity Agent  
Analyzes human photo and returns what must not change: face, body, proportions, pose.

5. Garment Identity Agent  
Analyzes clothing: type, color, cut, buttons, pockets, collar, sleeves, print, logo, texture.

6. Material / Texture Agent  
Visually estimates material but never claims exact composition without label, product description or trusted source.

7. Try-On Agent  
Creates virtual try-on result using human and garment constraints.

8. Product Card Agent  
Creates B2B product card content and visual package.

9. Fashion Stylist Agent  
Explains fit, style, proportions, colors, outfit ideas and use cases.

10. Marketplace Agent  
Finds similar, cheaper and alternative products through approved data sources.

11. Trend Agent  
Turns trend signals into practical recommendations for users and businesses.

12. Pricing Agent  
Analyzes price positioning using comparable products and business context.

13. Quality Verifier Agent  
Checks image/result quality before user sees it.

14. Repair Agent  
Fixes local issues without regenerating the entire result unnecessarily.

15. Cost / Credits Agent  
Calculates workflow cost, internal cost, credits, repair cost and margin.

## 9. Agent output rules

Agents must return structured data.

Preferred format:
- JSON;
- explicit confidence;
- explicit errors;
- explicit limitations;
- no vague marketing text.

Agent output must be usable by backend.

Bad output:
- long beautiful explanation without structure;
- hidden assumptions;
- invented facts;
- no confidence;
- no validation status.

Good output:
- structured JSON;
- clear decision;
- confidence;
- risks;
- next action;
- data that can be saved.

## 10. Quality system

Any generated image-result must pass Quality Verifier before user sees it.

Quality Verifier checks:
- face preservation;
- body preservation;
- pose preservation;
- garment similarity;
- color accuracy;
- buttons;
- pockets;
- collar;
- sleeves;
- logo / print;
- texture consistency;
- hands / fingers / neck / waist artifacts;
- background issues;
- overall realism.

Backend decision after quality check:
- pass;
- repair;
- retry;
- reject;
- ask user for better input.

User must not receive obvious broken results.

## 11. Repair / retry rules

Repair is used for local fixable issues:
- wrong color;
- missing button;
- missing pocket;
- broken collar;
- sleeve issue;
- background artifact;
- minor visual artifact.

Retry is used when the whole generation failed:
- person changed;
- body changed;
- wrong garment;
- impossible pose;
- severe distortion;
- result cannot be repaired locally.

If bad result is caused by our system, repair/retry should not charge the user again unless project billing rules explicitly say otherwise.

## 12. Credits logic

Credits are calculated by backend.

Credits may include:
- human analysis;
- garment analysis;
- material / texture analysis;
- image generation;
- quality verification;
- repair;
- retry;
- marketplace search;
- stylist explanation;
- product card generation;
- storage;
- margin.

Frontend only displays:
- current balance;
- estimated cost;
- final charged amount;
- refund / free repair status, if applicable.

Frontend must not calculate or modify credits.

## 13. Marketplace logic

Marketplace search must use legal and approved data sources.

Allowed sources:
- official APIs;
- partner feeds;
- seller uploaded catalog;
- manual catalog import;
- approved public links;
- approved connectors.

Do not build hidden scraping or bypass marketplace rules.

Google infrastructure can be used for connectors, storage, normalization, embeddings, search and price history.  
But Google does not magically provide marketplace inventory.  
Data source must be explicit.

## 14. Data storage

Use separate storage layers.

Firestore:
- users;
- user profiles;
- business profiles;
- job statuses;
- credits balance;
- job history;
- saved outfits;
- saved product cards;
- workflow events.

Cloud Storage:
- uploaded human photos;
- uploaded garment photos;
- product photos;
- masks;
- intermediate files;
- final images;
- quality reports;
- repair versions.

Cloud SQL / AlloyDB:
- products;
- product images;
- garment attributes;
- marketplace offers;
- competitor products;
- merchant catalogs;
- price snapshots;
- product card versions.

Vector Search / AlloyDB Vector:
- garment embeddings;
- product embeddings;
- visual similarity;
- semantic similarity.

BigQuery:
- analytics events;
- workflow cost;
- repair frequency;
- model quality;
- trends;
- conversion signals;
- margin analysis.

## 15. Frontend UI requirements

Every working page must have:
- loading state;
- empty state;
- error state;
- success state;
- validation errors;
- disabled state;
- responsive layout;
- accessible labels;
- real routes and actions.

Forms must have:
- visible labels;
- validation;
- disabled state during submit;
- backend error handling;
- double-submit protection.

Upload zones must have:
- file picker;
- drag-and-drop;
- file type validation;
- file size validation;
- preview;
- progress;
- error state;
- retry option.

Dashboard must not use hardcoded:
- user name;
- credits balance;
- history;
- tariffs;
- product cards;
- AI results.

## 16. Design direction

Visual style:
- premium fashion-tech;
- calm;
- clean;
- Apple-inspired;
- warm ivory background;
- white / silk cards;
- black primary CTA;
- violet only for AI / analysis / status;
- champagne / gold / beige only as subtle fashion accent.

Do not create:
- flashy AI generator UI;
- random neon style;
- anime / avatar / meme generator feeling;
- marketplace clutter;
- overdesigned dashboard.

Design system must be consistent:
- colors;
- typography;
- spacing;
- border radius;
- shadows;
- components;
- responsive behavior.

## 17. What not to build

AI FitFabrica must not become:
- universal AI image generator;
- avatar generator;
- anime filter;
- meme tool;
- logo generator;
- generic poster creator;
- random model showcase;
- frontend wrapper over image models;
- one-click model picker.

The product question is not:
"What can AI do with an image?"

The product question is:
"How can AI help a person or business make better clothing decisions?"

## 18. Development priorities

Do not start from random pages.

Correct preparation order:
1. agent sandbox;
2. capability testing;
3. agent contracts;
4. workflow specs;
5. data model;
6. backend API contracts;
7. quality rules;
8. credits logic;
9. frontend integration;
10. production polish.

Before building a full production workflow, test critical capabilities:
- Human Identity;
- Garment Identity;
- Material / Texture honesty;
- Try-On quality;
- Quality Verifier accuracy;
- Repair reliability;
- Marketplace data availability.

## 19. Definition of Done

A task is complete only if:

- it follows backend-first architecture;
- frontend/mobile stays thin;
- routes are real;
- buttons and forms are not fake;
- API integration goes through backend;
- errors are handled;
- data is typed;
- no secrets are exposed;
- no production values are hardcoded;
- upload flow validates files;
- loading/error/success states exist;
- generated image results go through quality logic;
- credits are not calculated on frontend;
- tests/checks pass where available;
- documentation is updated if contracts, routes or workflows changed.

If something cannot be completed, clearly state:
- what was done;
- what was not done;
- why;
- what is required next.