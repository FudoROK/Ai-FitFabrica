# AI FitFabrica Web

## Структура

- `src/app` — маршруты Next.js и layout'ы public/workspace
- `src/components` — переиспользуемые navigation и UI-компоненты
- `src/features` — page-level рендереры public и workspace
- `src/lib/content` — контент страниц без смешивания с JSX
- `src/lib/routes` — единая карта навигации
- `src/lib/api` — типизированные контракты интеграции
- `src/types` — общие типы frontend
- `public/site/screens` — все изображения сайта, взятые из `sait/scrin`

## Команды

- `npm install`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run dev`

## Backend Integration

- frontend reads `NEXT_PUBLIC_API_BASE_URL`
- use `apps/web/.env.firebase.example` as the first Firebase-hosted env template
- for the exact `Firebase Hosting -> GCP VM backend` path, use `docs/runbooks/firebase_hosting_to_gcp_vm_backend.md`
- current live backend URL is `https://api.fit.aisoulfabrica.com`
- Firebase Hosting serves the exported app from `apps/web/out` with `cleanUrls`, so workspace navigation uses static-hosting-safe links instead of Next app-router prefetch semantics
