# AI FitFabrica - что осталось сделать

Дата актуализации: 2026-07-08

Это короткий документ для владельца проекта. Он отвечает на вопрос: что сейчас реально готово, что нельзя проверить без включенного биллинга/provider access, и что делать сразу после восстановления billing.

## Главный статус

Проект локально подготовлен к pre-billing клиентскому тестированию. Backend и frontend больше не находятся в состоянии "сырого прототипа": основные B2C/B2B контуры имеют реальные routes, typed API contracts, backend-owned persistence, fail-closed auth/billing behavior, readiness gates и acceptance-команды.

Проект еще не считается готовым к paid production запуску, потому что внешние системы не включены:

- production auth provider;
- billing/payment provider;
- Google/Gemini/Vertex provider access;
- approved live marketplace/search sources;
- deployed staging live acceptance после включения внешних систем.

До включения биллинга цель простая: не добавлять хаотично новые фичи, а держать проект чистым, проверяемым и готовым к спокойному post-billing acceptance.

## Текущая проверенная картина

Последний локальный baseline:

- `scripts/no_billing_acceptance_gate.py`: `readiness_status=ready`.
- `scripts/no_billing_acceptance_gate.py --full-backend --skip-frontend-build`: `readiness_status=ready`.
- Full backend suite: `1201 passed, 2 warnings`.
- Frontend `typecheck`, `lint`, `build`: passed.
- `scripts/client_readiness_gate.py`: B2C/B2B contours ready for no-billing testing.
- `scripts/auth_readiness_gate.py`: auth fails closed until provider activation.
- `scripts/billing_readiness_gate.py`: billing core is backend-owned and disabled before activation.
- `scripts/production_infrastructure_readiness_gate.py`: production env cannot silently use sandbox/in-memory infrastructure.
- `scripts/production_fallback_usage_audit.py`: runtime fallback usage is reviewed and guarded.
- `scripts/web_dependency_audit.py --require-ready`: ready; current npm audit has `0 high`, `0 critical`, `1 low`, `4 moderate`.
- `scripts/post_billing_acceptance_gate.py`: local artifacts ready; deployed `/ready` check is skipped until an API URL/token are provided.
- Git baseline is clean: рабочее дерево чистое after the latest pushed commits.

Known non-blocking noise:

- Authlib deprecation warning from dependency code.
- Intermittent `RuntimeError: Event loop is closed` warning from `aiosqlite` thread cleanup after tests. It does not fail the suite, but it is a polish item.

## Что уже готово для B2C

### Public entry

- Public routes exist: `/`, `/for-you`, `/business`, `/features`, `/pricing`, `/how-it-works`, `/about`, `/contact`, `/privacy`, `/login`.
- Contact/demo requests persist through backend SQL.
- Sign-in fails closed while production auth is disabled.
- Frontend does not fake OAuth/session success.

### Try-On

- Workspace routes exist for creating and viewing Try-On jobs.
- Backend owns job creation, validation, SQL persistence, lifecycle, quality/repair contracts and result state.
- No browser code calls AI providers directly.
- Before billing, sandbox/no-paid contour is testable.
- After billing, live generation, paid quality verification, repair and credit charging must be accepted on staging.

### Similar Search

- `/workspace/similar-search` has real request/photo search UI.
- Backend owns garment-photo request, search/ranking, local catalog fallback and click event persistence.
- Hidden scraping is not enabled.
- After billing/provider/source activation, live marketplace/search-source coverage must be accepted.

### Outfit Builder

- Route and backend request/status contract exist.
- Frontend has loading/error/empty/success handling.
- Live stylist/provider output remains blocked until provider activation.

## Что уже готово для B2B

### Business Catalog

- Merchant/product/catalog import contours exist.
- Product images, submit-to-review, admin approve/reject/archive and SQL persistence are implemented.
- Discovery candidates have durable SQL persistence and review statuses.
- Category validation and admin review are guarded.
- Live AI category validation remains blocked until provider billing/access is restored.

### Product Card

- Backend job creation, SQL persistence and mandatory garment-analysis contract exist.
- Frontend actions call backend instead of presenting fake final output.
- Live AI copy/image acceptance remains post-billing work.

### Content Package

- Backend job contract, SQL persistence and artifact metadata exist.
- Frontend action wiring and states exist.
- Live provider output and charging remain post-billing work.

### Pricing

- Backend-owned pricing job workflow exists.
- Frontend displays backend DTOs only.
- Live comparable-source coverage and charged pricing workflows remain post-billing work.

### Admin Review

- Admin readiness, business catalog, taxonomy and business-account pages exist.
- Backend admin routes fail closed and require configured access.
- Final production admin sign-in model still depends on auth activation.

## Что делать сразу после включения billing/provider access

Run these from the repository root after env is configured:

```powershell
.venv\Scripts\python.exe scripts\post_billing_acceptance_gate.py `
  --api-base-url "https://api.fit.aisoulfabrica.com" `
  --status-token "<STATUS_ENDPOINT_TOKEN>" `
  --require-ready

.venv\Scripts\python.exe scripts\platform_foundation_smoke.py --require-ready
.venv\Scripts\python.exe scripts\auth_readiness_gate.py
.venv\Scripts\python.exe scripts\billing_readiness_gate.py
.venv\Scripts\python.exe scripts\production_infrastructure_readiness_gate.py --require-production
.venv\Scripts\python.exe scripts\production_fallback_usage_audit.py --require-ready
.venv\Scripts\python.exe scripts\web_dependency_audit.py --require-ready
.venv\Scripts\python.exe scripts\business_catalog_search_index_readiness.py --require-db
.venv\Scripts\python.exe scripts\try_on_real_activation_smoke.py --require-ready
.venv\Scripts\python.exe scripts\business_catalog_staging_smoke.py
```

Then copy:

```text
docs/reports/templates/post_billing_live_acceptance_template.md
```

to:

```text
docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md
```

and record live results there.

## Что нельзя делать сейчас

- Не включать real customer production до post-billing acceptance.
- Не давать frontend прямой доступ к AI providers.
- Не считать credits на frontend.
- Не включать скрытый scraping marketplace/Instagram.
- Не обходить backend quality verifier/repair/retry decisions.
- Не добавлять новые in-memory/fake runtime fallbacks без review.
- Не запускать `npm audit fix --force` без отдельного review, потому что это может изменить dependency baseline.

## Следующий полезный no-billing блок

1. Убрать test warning `Event loop is closed`, чтобы full backend suite был не только passing, но и без шумных thread warnings.
2. Обновить более глубокие технические документы (`00_PROJECT_MASTER_PLAN.md`, `02_TECHNICAL_PROJECT_MAP.md`, `03_AGENT_SYSTEM_GUIDE.md`) только если они мешают onboarding. Сейчас owner truth уже находится в этом документе и readiness runbooks.
3. Декомпозировать самые большие runtime/frontend файлы только при работе в соответствующей области, не делать случайный большой refactor перед billing.

## Простыми словами

Сейчас проект не нужно расширять вширь. Его нужно держать в чистом состоянии до включения биллинга.

Когда billing/provider access восстановлен, мы не начинаем "доделывать проект с нуля"; мы запускаем подготовленные gates, live acceptance и фиксируем только реальные проблемы, которые проявятся на платных provider flows.
