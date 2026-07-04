# Деплой AI FitFabrica: backend и сайт

Этот runbook предназначен для staging-окружения:

- GCP project: `ai-fitfabrica`
- VM: `fitfabrica-staging-vm`
- zone: `europe-west1-b`
- backend: `https://api.fit.aisoulfabrica.com`
- frontend: `https://fit.aisoulfabrica.com`
- Firebase project: `ai-fitfabrica`

Все локальные команды выполняются в PowerShell.

## 1. Перейти в проект

```powershell
cd "C:\Code\Ai Fitfabrica"
```

## 2. Проверить авторизацию и доступ

```powershell
gcloud config set account admin@aisoulfabrica.com
gcloud config set project ai-fitfabrica
gcloud config set compute/zone europe-west1-b

gcloud auth list
firebase projects:list

gcloud compute ssh ubuntu@fitfabrica-staging-vm `
  --zone=europe-west1-b `
  --command="echo SSH_READY"
```

## 3. Проверить проект перед деплоем

```powershell
cd "C:\Code\Ai Fitfabrica"

.venv\Scripts\python.exe scripts/no_billing_acceptance_gate.py

.venv\Scripts\python.exe scripts/client_readiness_gate.py

.venv\Scripts\python.exe scripts\check_architecture.py
.venv\Scripts\python.exe -m compileall -q src
.venv\Scripts\python.exe -m pytest -q -x --maxfail=1

cd "C:\Code\Ai Fitfabrica\apps\web"
npm ci
npm run lint
npm run typecheck
npm run build
```

Не продолжать деплой, если любая проверка завершилась ошибкой.

## 4. Создать backend-архив

Архив не должен содержать локальные секреты, виртуальное окружение, Git-историю или frontend build.

```powershell
cd "C:\Code\Ai Fitfabrica"

.\scripts\create_backend_deploy_archive.ps1 -OutputPath backend-deploy.tar.gz

Get-FileHash backend-deploy.tar.gz -Algorithm SHA256
```

## 5. Загрузить backend на VM

```powershell
cd "C:\Code\Ai Fitfabrica"

gcloud compute scp backend-deploy.tar.gz `
  ubuntu@fitfabrica-staging-vm:/tmp/backend-deploy.tar.gz `
  --zone=europe-west1-b
```

## 6. Сделать backup и развернуть backend

Команда сохраняет текущие файлы приложения, распаковывает новую версию, пересобирает контейнеры и применяет миграции.

```powershell
gcloud compute ssh ubuntu@fitfabrica-staging-vm `
  --zone=europe-west1-b `
  --command="bash -lc 'set -euo pipefail; cd /opt/fitfabrica; mkdir -p backups; tar -czf backups/before-deploy-`$(date +%Y%m%d-%H%M%S).tar.gz src alembic scripts Dockerfile docker-compose.portable-staging.yml 2>/dev/null || true; tar -xzf /tmp/backend-deploy.tar.gz -C /opt/fitfabrica; bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local; docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local ps'"
```

## 7. Проверить backend

Публичная проверка:

```powershell
$health = Invoke-WebRequest `
  -UseBasicParsing `
  -Uri "https://api.fit.aisoulfabrica.com/health" `
  -TimeoutSec 30

$health.StatusCode
$health.Content
```

Проверка контейнеров, миграций и ошибок:

```powershell
gcloud compute ssh ubuntu@fitfabrica-staging-vm `
  --zone=europe-west1-b `
  --command="bash -lc 'cd /opt/fitfabrica; docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local ps; docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local exec -T api alembic current; docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local logs --tail=150 api worker'"
```

Ожидаемый результат:

- `api` имеет статус `healthy`;
- `worker` имеет статус `healthy`;
- Alembic показывает текущую миграцию с пометкой `(head)`;
- в последних логах нет новых traceback или необработанных ошибок.

## 8. Собрать сайт

Frontend должен обращаться к публичному backend.

```powershell
cd "C:\Code\Ai Fitfabrica\apps\web"

$env:NEXT_PUBLIC_API_BASE_URL="https://api.fit.aisoulfabrica.com"
$env:NEXT_PUBLIC_ENABLE_ADMIN_READINESS_UI="true"
$env:NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI="true"
$env:NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI="true"
$env:NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI="true"

npm ci
npm run lint
npm run typecheck
npm run build
```

Статическая сборка должна появиться в:

```text
C:\Code\Ai Fitfabrica\apps\web\out
```

## 9. Опубликовать сайт в Firebase Hosting

```powershell
cd "C:\Code\Ai Fitfabrica"

firebase deploy --only hosting --project ai-fitfabrica
```

## 10. Проверить сайт после публикации

```powershell
$site = Invoke-WebRequest `
  -UseBasicParsing `
  -Uri "https://fit.aisoulfabrica.com/" `
  -TimeoutSec 30

$workspace = Invoke-WebRequest `
  -UseBasicParsing `
  -Uri "https://api.fit.aisoulfabrica.com/api/workspace/bootstrap" `
  -TimeoutSec 30

"site=$($site.StatusCode)"
"workspace=$($workspace.StatusCode)"
```

Оба запроса должны вернуть `200`.

## 10.1 No-billing staging smoke

Этот smoke не вызывает платные AI/provider workflow. Он проверяет безопасные публичные поверхности после деплоя: `/health`, `/ready`, workspace bootstrap, fail-closed auth, public site routes, B2C workspace routes, B2B workspace routes и admin readiness/review routes.

```powershell
cd "C:\Code\Ai Fitfabrica"

.venv\Scripts\python.exe scripts/staging_no_billing_smoke.py `
  --api-base-url "https://api.fit.aisoulfabrica.com" `
  --web-base-url "https://fit.aisoulfabrica.com" `
  --status-token "<STATUS_ENDPOINT_TOKEN>"
```

Ожидаемый результат:

- `readiness_status` = `ready`;
- `failed_checks` пустой;
- `/auth/sign-in` возвращает fail-closed `503`, пока production auth не подключён.

Опционально, если нужно проверить запись публичной заявки в SQL:

```powershell
.venv\Scripts\python.exe scripts/staging_no_billing_smoke.py `
  --api-base-url "https://api.fit.aisoulfabrica.com" `
  --web-base-url "https://fit.aisoulfabrica.com" `
  --status-token "<STATUS_ENDPOINT_TOKEN>" `
  --include-demo-request
```

## 11. Удалить временный архив

Локально:

```powershell
Remove-Item -LiteralPath "C:\Code\Ai Fitfabrica\backend-deploy.tar.gz" -Force
```

На VM:

```powershell
gcloud compute ssh ubuntu@fitfabrica-staging-vm `
  --zone=europe-west1-b `
  --command="rm -f /tmp/backend-deploy.tar.gz"
```

## 12. Быстрый повторный деплой только backend

Использовать только после успешных локальных проверок.

```powershell
cd "C:\Code\Ai Fitfabrica"

.\scripts\create_backend_deploy_archive.ps1 -OutputPath backend-deploy.tar.gz

gcloud compute scp backend-deploy.tar.gz ubuntu@fitfabrica-staging-vm:/tmp/backend-deploy.tar.gz --zone=europe-west1-b

gcloud compute ssh ubuntu@fitfabrica-staging-vm --zone=europe-west1-b --command="bash -lc 'set -euo pipefail; cd /opt/fitfabrica; mkdir -p backups; tar -czf backups/before-deploy-`$(date +%Y%m%d-%H%M%S).tar.gz src alembic scripts 2>/dev/null || true; tar -xzf /tmp/backend-deploy.tar.gz -C /opt/fitfabrica; bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local'"

Invoke-WebRequest -UseBasicParsing "https://api.fit.aisoulfabrica.com/health"

Remove-Item -LiteralPath "C:\Code\Ai Fitfabrica\backend-deploy.tar.gz" -Force
```

## 13. Быстрый повторный деплой только сайта

```powershell
cd "C:\Code\Ai Fitfabrica\apps\web"

$env:NEXT_PUBLIC_API_BASE_URL="https://api.fit.aisoulfabrica.com"
$env:NEXT_PUBLIC_ENABLE_ADMIN_READINESS_UI="true"
$env:NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI="true"
$env:NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI="true"
$env:NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI="true"

npm ci
npm run lint
npm run typecheck
npm run build

cd "C:\Code\Ai Fitfabrica"
firebase deploy --only hosting --project ai-fitfabrica

Invoke-WebRequest -UseBasicParsing "https://fit.aisoulfabrica.com/"
```

## 14. Откат backend

Сначала посмотреть доступные backup-архивы:

```powershell
gcloud compute ssh ubuntu@fitfabrica-staging-vm `
  --zone=europe-west1-b `
  --command="ls -lt /opt/fitfabrica/backups | head -20"
```

Затем заменить `<BACKUP_FILE>` на нужный архив:

```powershell
gcloud compute ssh ubuntu@fitfabrica-staging-vm `
  --zone=europe-west1-b `
  --command="bash -lc 'set -euo pipefail; cd /opt/fitfabrica; tar -xzf backups/<BACKUP_FILE> -C /opt/fitfabrica; docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local up --build -d api worker; docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local ps'"
```

После отката обязательно проверить:

```powershell
Invoke-WebRequest -UseBasicParsing "https://api.fit.aisoulfabrica.com/health"
```

## 15. B2B Catalog staging smoke

После backend-деплоя и миграций проверить бизнес-каталог отдельным smoke:

```powershell
cd "C:\Code\Ai Fitfabrica"

.venv\Scripts\python.exe scripts/business_catalog_staging_smoke.py `
  --base-url "https://api.fit.aisoulfabrica.com"
```

Что проверяет smoke:

- `/health`;
- merchant save/read;
- product create/list;
- product image upload;
- submit-to-review;
- CSV import/status/errors;
- admin tier gate enabled или disabled.

Если admin business catalog должен быть включён на staging, запускать:

```powershell
.venv\Scripts\python.exe scripts/business_catalog_staging_smoke.py `
  --base-url "https://api.fit.aisoulfabrica.com" `
  --require-admin-enabled
```

## 16. B2B Search Index readiness после deploy

После backend deploy и `alembic upgrade head` проверить, что новый контур индексации каталога готов:

```powershell
gcloud compute ssh ubuntu@fitfabrica-staging-vm `
  --zone=europe-west1-b `
  --command="bash -lc 'cd /opt/fitfabrica; docker compose -f docker-compose.portable-staging.yml --env-file .env.portable-remote-staging.local exec -T api python scripts/business_catalog_search_index_readiness.py --require-db'"
```

Ожидаемый результат:

- `readiness_status` = `ready`;
- `migration` = `passed`;
- `worker_handler` = `passed`;
- `indexing_workflow` = `passed`;
- `db_schema` = `passed`.
