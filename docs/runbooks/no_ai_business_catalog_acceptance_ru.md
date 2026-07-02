# No-AI acceptance B2B каталога

Дата: 2026-07-02

## Зачем нужен этот прогон

Этот прогон проверяет B2B catalog workflow без платных Gemini/Vertex вызовов.

Проверяется цепочка:

1. Импорт товаров из CSV.
2. Загрузка изображений.
3. Submit товаров на admin review.
4. Backend category validation в режиме `sandbox`.
5. Approve только товаров со статусом `matched`.
6. Search indexing.
7. Structured Similar Search без `/garment-photo`.

Важно: `/api/similar-search/garment-photo` в этом прогоне не используется, потому что он вызывает Garment Identity Agent и требует Gemini.

## Настройка staging

На staging VM должен быть включён режим:

```env
BUSINESS_CATALOG_CATEGORY_VALIDATION_MODE=sandbox
```

Этот режим разрешён только для staging/dev acceptance. Он не должен использоваться как production AI-анализ.

## Что считается успешным результатом

Успешный результат:

- API `/health` возвращает `healthy`;
- CSV импортируется без rejected rows;
- все картинки загружаются;
- все товары отправляются на review;
- category validation не падает;
- товары со статусом `matched` проходят approve;
- mismatched/uncertain товары остаются заблокированными;
- approved товары индексируются;
- structured Similar Search возвращает товары с `image_url`.

Если тест-пак содержит неправильные категории, это не ошибка backend. Например, если файл называется `skirt`, а CSV category указана `dress`, gate должен оставить товар в `mismatch`.

## Команда локального loader

Для полного прогона с заведомо несовершенным тест-паком:

```powershell
$env:FITFABRICA_ADMIN_API_TOKEN="<admin-token>"
.venv\Scripts\python.exe scripts\load_realistic_business_catalog_staging.py `
  --base-url https://api.fit.aisoulfabrica.com `
  --pack-dir "C:\Madi\00 Мой Бизнес\Ai_FitFabrica\fitfabrica_realistic_clothing_test_pack\_import_ready" `
  --poll-index-seconds 180 `
  --allow-category-blocks
Remove-Item Env:\FITFABRICA_ADMIN_API_TOKEN
```

Без `--allow-category-blocks` loader обязан падать, если category gate нашёл mismatch/uncertain товары.

## VM runner

Если тест-пак уже загружен на VM в `/tmp/fitfabrica_catalog_acceptance/import_ready`, можно запускать:

```bash
bash /tmp/fitfabrica_catalog_acceptance/run_staging_no_ai_catalog_acceptance.sh
```

Runner берёт `ADMIN_API_TOKEN` из env контейнера API и не печатает его.

## Cleanup

После acceptance временные товары нужно архивировать, а не удалять из БД.

Использовать cleanup script:

```powershell
$env:FITFABRICA_ADMIN_API_TOKEN="<admin-token>"
.venv\Scripts\python.exe scripts\cleanup_staging_catalog_acceptance_products.py `
  --base-url https://api.fit.aisoulfabrica.com `
  --created-at-prefix "2026-07-02T08:15"
Remove-Item Env:\FITFABRICA_ADMIN_API_TOKEN
```

После cleanup:

- временные файлы на VM удалить;
- backend deploy archive удалить;
- проверить `/health`;
- остановить VM.

## Что не проверяет no-AI прогон

Этот прогон не проверяет:

- Garment Identity Agent качество;
- Gemini billing/access;
- real `/garment-photo` Similar Search;
- image generation;
- paid Try-On;
- production model quality.

Для этого нужен отдельный платный live acceptance после восстановления billing/provider access.
